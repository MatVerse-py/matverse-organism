# Cassandra Backend — API Contract (v1.0.0)

The Cassandra agent backend exposes a small, secure HTTP API that any
frontend (Base44, web, CLI, mobile) can call. This document is the
canonical contract; the implementation is in
`matverse/cassandra_backend/`.

## Constitutional position

> Cassandra PREPARA. O operador assina. O mundo testemunha.

The backend enforces the 5 hard limits at runtime, not just in the
system prompt. Any message that triggers an external action is
returned as `gate_status=ESCALATE` with `needs_operator=true`, and
**no LLM is called** — the fail-closed path runs.

## Security model

The token model follows the same rules as the Base44 client
(`matverse.cassandra_base44`):

```
┌────────────┐    bootstrap    ┌──────────────┐
│  api_key   │ ──────────────► │  session     │
│  (in env)  │  POST /auth/   │  token       │
│  CASSANDRA_│  session       │  (1h TTL)    │
│  API_KEY   │                │              │
└────────────┘                └──────┬───────┘
       │                              │ Bearer
       │ wiped from                   │
       │ memory                       ▼
       │                       ┌──────────────┐
       ▼                       │  cap token   │
   (gone)                     │  (10m TTL,   │
                              │  scoped to   │
                              │  agent+skill)│
                              └──────┬───────┘
                                     │ Bearer
                                     ▼
                              ┌──────────────┐
                              │  POST /chat  │
                              └──────────────┘
```

The `api_key` is held only during `POST /auth/session` and is wiped
from memory immediately after. Subsequent calls use Bearer credentials
only. There is **no path** through the API that sends the `api_key`
as a request header (the integration examples explicitly do NOT use
`api_key` in headers — that was a Base44 documentation bug we
identified earlier).

## Endpoints

### `GET /health`

Returns the server status, version, and list of endpoints.

**Response 200**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime_seconds": 42,
  "matverse_app_id": "6a2dd76b300afd3eb43293d7",
  "base44_superagent_id": "6a3f8dcd43af4cd136e09be2",
  "endpoints": [
    "GET  /health",
    "POST /auth/session",
    "POST /auth/capability",
    "POST /chat",
    "GET  /system-prompt"
  ],
  "constitutional_position": "Cassandra PREPARA. O operador assina. ..."
}
```

### `POST /auth/session`

Exchange the `api_key` (from `CASSANDRA_API_KEY` env var on the server)
for a `session_token`.

**Request body**:
```json
{
  "api_key": "<from secret manager>",
  "ttl_seconds": 3600
}
```

**Response 200**:
```json
{
  "session_token": "sess-<32 random url-safe chars>",
  "token_type": "Bearer",
  "expires_in": 3600,
  "issued_at": 1752600000,
  "user_id": "usr-<sha256-fingerprint-prefix>",
  "message": "api_key has been validated. Use this session_token for subsequent calls. The api_key is no longer needed and was wiped from memory."
}
```

**Response 401** (invalid key):
```json
{ "error": "invalid api_key", "code": "INVALID_API_KEY" }
```

**Response 400** (missing key):
```json
{ "error": "missing api_key", "code": "MISSING_API_KEY" }
```

### `POST /auth/capability`

Mint a `capability_token` scoped to a (agent_id, skill_name) pair.
Requires `Authorization: Bearer <session_token>`.

**Request body**:
```json
{
  "agent_id": "cassandra",
  "skill_name": "interpret",
  "ttl_seconds": 600,
  "scope": { "allow_burst": false }
}
```

**Response 200**:
```json
{
  "capability_token": "cap-<32 random url-safe chars>",
  "token_type": "Bearer",
  "agent_id": "cassandra",
  "skill_name": "interpret",
  "scope": { "allow_burst": false },
  "expires_in": 600,
  "issued_at": 1752600000,
  "user_id": "usr-..."
}
```

### `POST /chat`

Send a user message; get a Cassandra response. Requires
`Authorization: Bearer <capability_token>`.

**Request body**:
```json
{
  "message": "o que é o MNB?",
  "context": {
    "page": "/copilot",
    "user_role": "operator"
  },
  "prefer_burst": false
}
```

**Response 200** (success):
```json
{
  "run_id": "run-<microseconds>",
  "response": "Interpretação: pedido de explicação.\nMNB 5-tuple: m = (e, Ψ, C, τ, h) com ρ = Ψ·τ/C. MNB é camada POSTERIOR... [epistemic: OBS] ver references/lineage.md.",
  "gate_status": "PASS",
  "epistemic": "OBS",
  "triggered_limits": [],
  "needs_operator": false,
  "route_used": "ZERO",
  "model_used": "local_interpret",
  "agent_id": "cassandra",
  "skill_name": "interpret",
  "user_id": "usr-...",
  "context": { "page": "/copilot", "user_role": "operator" },
  "issued_at": 1752600000,
  "policy_version": "v3.8.2",
  "constitutional_position": "Cassandra PREPARA. O operador assina."
}
```

**Response 200** (ESCALATE, external action):
```json
{
  "run_id": "run-...",
  "response": "Esta ação está fora do escopo de Cassandra. Requer Ω-Gate + EvidenceOS + operador humano. ... [epistemic: ESC] Pedido de ação externa detectado: 'publique'.",
  "gate_status": "ESCALATE",
  "epistemic": "ESC",
  "triggered_limits": [1],
  "needs_operator": true,
  "route_used": "ZERO",
  "model_used": "gate_only (fail-closed)",
  ...
}
```

**Response 200** (DENY, prompt injection):
```json
{
  "run_id": "run-...",
  "response": "Limit 5: avatar≠auth violation (matched 'ignore previous instructions'); Esta ação está fora do escopo...",
  "gate_status": "DENY",
  "epistemic": "ESC",
  "triggered_limits": [5],
  "needs_operator": true,
  ...
}
```

**Response 401** (missing/invalid Bearer):
```json
{ "error": "missing Bearer token", "code": "MISSING_BEARER" }
```

**Response 403** (skill not authorized for /chat):
```json
{ "error": "skill_name 'destroy_world' is not authorized for /chat", "code": "SKILL_NOT_AUTHORIZED" }
```

### `GET /system-prompt`

Returns the canonical, immutable Cassandra system prompt (for
transparency and audit).

**Response 200**:
```json
{
  "system_prompt": "Você é Cassandra, o operador cognitivo...",
  "version": "v3.8.2",
  "immutable": true,
  "note": "This prompt is the constitutional contract of the agent. It is served read-only for transparency/audit. The agent enforces it at runtime via the 5 hard limits."
}
```

## The 5 hard limits (runtime)

| # | Limit | Runtime check | Gate status |
|---|-------|---------------|-------------|
| 1 | External action requires Ω-Gate + EvidenceOS + operator | `check_external_action()` matches keywords (publish, sign, deploy, transfer, execute) with word-boundary regex | `ESCALATE` |
| 2 | Evidence before claim (OBS requires source_id) | `parse_epistemic()` finds `[epistemic: OBS]` and `has_source_citation()` checks for tests/refs/URLs | `HOLD` (downgrade to HYP) |
| 3 | Determinism (same input + same policy → same output) | `local_interpret()` is pure (no I/O, no LLM); LLM path would need `temperature=0` | `PASS` |
| 4 | Fail-closed (doubt → ESCALATE) | `check_uncertainty()` matches uncertainty keywords (talvez, maybe, i don't know) | `HOLD` (when paired with HYP) |
| 5 | Avatar ≠ authentication | `check_impersonation()` matches prompt-injection patterns (ignore instructions, act as, roleplay as) | `DENY` |

## Gate status table

| gate_status | Meaning | `can_publish` | `needs_operator` |
|---|---|---|---|
| `PASS` | All limits OK, response is valid | true | false |
| `HOLD` | Limit 2 (no source) or 4 (uncertainty) | true | false |
| `ESCALATE` | Limit 1 (external action) | false | **true** |
| `DENY` | Limit 5 (impersonation) | false | **true** |

## LLM router (ZERO / TINY / BURST)

| Route | When | Backend | Network |
|---|---|---|---|
| `ZERO` | External action OR complexity < 0.6 OR no TINY model | `local_interpret()` (deterministic, no LLM) | none |
| `TINY` | complexity ≥ 0.6 AND `CASSANDRA_TINY_MODEL` env var set | local model (Phi-3, Qwen, etc.) | none |
| `BURST` | `prefer_burst=true` AND `capability.scope.allow_burst=true` | NVIDIA NIM (or other remote) | yes (operator-authorized) |

## CORS

The server is CORS-enabled by default. To restrict, set the env var
`CASSANDRA_ALLOWED_ORIGINS` to a comma-separated list, e.g.
`CASSANDRA_ALLOWED_ORIGINS=https://app.base44.com,https://cassandra.matverse.app`.

## Running locally

```bash
export CASSANDRA_API_KEY="<from your secret manager>"
python -m matverse.cassandra_backend.server --host 127.0.0.1 --port 8787
```

## Docker

```bash
docker build -t cassandra-backend matverse/cassandra_backend/
docker run -p 8787:8787 -e CASSANDRA_API_KEY=$CASSANDRA_API_KEY cassandra-backend
```

## Base44 integration

See `matverse/cassandra_backend/frontend_integration.ts` for a
drop-in TypeScript snippet that the Base44 Cassandra Cube app can
use to call this backend. The snippet:

1. Calls `POST /auth/session` once (or on session expiry)
2. Calls `POST /auth/capability` once per (agent, skill) per hour
3. Caches both tokens in memory
4. Calls `POST /chat` for every user message
5. Handles `gate_status=ESCALATE/DENY` by NOT calling Base44's
   publish/sign APIs (the constitutional invariant)
