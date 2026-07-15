# Cassandra Backend

A self-contained HTTP backend for the Cassandra agent. Pure Python
stdlib, zero external dependencies, runs anywhere Python 3.8+ runs.

This is the backend that the Base44 "Cassandra Cube" app (or any
other frontend) calls to converse with the constitutional Cassandra
agent.

## Quickstart

```bash
# 1. Set the api_key (from your secret manager)
export CASSANDRA_API_KEY="<from secret manager>"

# 2. Run the server
python -m matverse.cassandra_backend.server --host 127.0.0.1 --port 8787

# 3. Test it
curl http://127.0.0.1:8787/health
```

## Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | none | Server status |
| GET | `/system-prompt` | none | Canonical system prompt (read-only) |
| POST | `/auth/session` | api_key (one-time) | Bootstrap: api_key → session_token |
| POST | `/auth/capability` | Bearer session_token | Mint capability_token for (agent, skill) |
| POST | `/chat` | Bearer capability_token | Send a user message, get a response |

## Security model

The api_key is read once, exchanged for a session_token, and wiped
from memory. All subsequent calls use Bearer credentials. The
capability_token is scoped per (agent, skill) and is time-limited.

The 5 hard limits are enforced at runtime:

1. **External action** (publish, sign, deploy, transfer) → ESCALATE
2. **OBS without source** → HOLD, downgrade to HYP
3. **Determinism** (local_interpret is pure, no LLM by default)
4. **Uncertainty** → HOLD
5. **Impersonation** (prompt injection) → DENY

## Tests

```bash
python -m unittest tests.test_cassandra_backend
```

57 tests covering: policy (5 limits), router (ZERO/TINY/BURST),
local_interpret, system prompt, token store, HTTP end-to-end,
security invariants.

## API contract

See `../../references/cassandra_backend_api.md` for the full contract.

## Base44 integration

See `frontend_integration.ts` for a drop-in TypeScript snippet that
the Base44 Cassandra Cube app can use to call this backend.

The snippet:
1. Calls `/auth/session` once (on bootstrap, with api_key from env)
2. Caches `session_token` for 1 hour
3. Calls `/auth/capability` once per (agent, skill) pair per 10 min
4. Caches `capability_token` accordingly
5. Calls `/chat` for every user message
6. Exposes `assertConstitutionalGate()` to block any Base44
   mutation when the gate is ESCALATE or DENY

## Docker

```bash
docker build -t cassandra-backend matverse/cassandra_backend/
docker run -p 8787:8787 -e CASSANDRA_API_KEY=$CASSANDRA_API_KEY cassandra-backend
```

The Dockerfile uses python:3.11-slim, runs as non-root user, and
includes a healthcheck. The api_key is passed at runtime, never
baked into the image.

## Constitutional position

> Cassandra PREPARA. O operador assina. O mundo testemunha.

The backend never authorizes external action. If the user asks
Cassandra to "publish", "sign", "deploy", "transfer", or "execute",
the response is `gate_status=ESCALATE` with `needs_operator=true`,
and **no LLM is called**. The fail-closed path runs.

## Versioning

- v1.0.0 (2026-07-15): initial release. Aligned with
  matverse-organism v3.8.2 and Base44 app 6a3f8b077390fd927d6fd4bf.

## Related

- `matverse/cassandra_prompt.py` — canonical system prompt
- `matverse/cassandra_base44.py` — Base44 client (uses the same
  session/capability token model; this backend is the server side)
- `matverse/cassandra_agent.py` — high-level agent API
- `references/cassandra_base44_integration.md` — Base44 client docs
- `references/cassandra_backend_api.md` — this backend's contract
