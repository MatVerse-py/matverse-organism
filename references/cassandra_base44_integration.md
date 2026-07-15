# Cassandra ⇄ Base44 — Security-First Integration (v3.8.2)

This document describes how the Cassandra agent (`matverse.cassandra_agent`)
integrates with the Base44 app `6a2dd76b300afd3eb43293d7` (MatVerse URANO
OSX). The integration follows the constitutional security model.

## Constitutional Security Model

The agent must NEVER hold a permanent API key. The credential lifecycle is:

```
┌────────────┐    bootstrap    ┌──────────────┐
│  api_key   │ ──────────────► │  SessionToken │
│  (in env)  │  POST /auth/    │  (time-limited)│
└────────────┘   session       └──────┬────────┘
       │                               │ Bearer
       │ wiped from                    │
       │ memory after                  ▼
       │ bootstrap              ┌────────────────┐
       ▼                        │  All other     │
   (gone)                      │  calls         │
                               └──────┬─────────┘
                                      │ scope: agent+skill
                                      ▼
                               ┌────────────────┐
                               │ CapabilityToken│
                               │ (time-limited, │
                               │  per agent+skill)│
                               └────────────────┘
```

**Hard limits (encoded in `CASSANDRA_SYSTEM_PROMPT`):**

1. `api_key` is read from `BASE44_API_KEY` env var ONLY at `__init__` time.
2. It is exchanged for a `SessionToken` via `POST /auth/session` immediately.
3. After `authenticate()`, the `api_key` attribute is set to `None` (wiped
   from memory).
4. All subsequent entity calls use `Authorization: Bearer <session_token>`.
5. Agent conversations use `CapabilityToken` (scoped to `agent_id` +
   `skill_name`, TTL = 10 min by default).
6. The `api_key` is NEVER sent as a request header on any call other than
   the initial `POST /auth/session` bootstrap.

This matches the constitutional rule:

> frontend         → never contains api_key permanent
> backend / SM     → stores the credential
> session          → receives a temporary, limited token
> agent            → receives a capability token, not the main key

## Token classes

```python
@dataclass
class SessionToken:
    token: str
    issued_at: int
    ttl_seconds: int       # default 3600 (1 hour)
    user_id: str = ""

@dataclass
class CapabilityToken:
    token: str
    agent_id: str
    skill_name: str        # bound to one (agent, skill) pair
    issued_at: int
    ttl_seconds: int       # default 600 (10 min)
    scope: Dict[str, Any]  # server-side validated
```

## Endpoints used

| Method | Path | Auth |
|--------|------|------|
| POST | `/auth/session` | `api_key` header (one-time bootstrap) |
| POST | `/auth/capability` | `Bearer <session_token>` |
| GET | `/entities/{name}` | `Bearer <session_token>` |
| POST | `/entities/{name}` | `Bearer <session_token>` |
| GET | `/entities/{name}/{id}` | `Bearer <session_token>` |
| PUT | `/entities/{name}/{id}` | `Bearer <session_token>` |
| GET | `/apps/{id}/agents/conversations` | `Bearer <capability_token>` |
| POST | `/apps/{id}/agents/conversations` | `Bearer <capability_token>` |
| POST | `/apps/{id}/agents/conversations/{cid}/messages` | `Bearer <capability_token>` |

## Five hard limits (constitutional)

Encoded in the system prompt; verifiable at runtime:

| # | Limit | Runtime check |
|---|-------|---------------|
| 1 | External action requires Ω-Gate + EvidenceOS + operator | `chat()` detects `execute`/`publique`/`assine`/`transfira`/`deploy` keywords → returns ESCALATE |
| 2 | OBS claim requires source_id | epistemic parser requires `[epistemic: OBS]` + source citation |
| 3 | Determinism under policy_version | `local_interpret()` is pure (no LLM, no I/O) |
| 4 | Fail-closed on doubt | `_classify_gate` returns ESCALATE on any uncertainty keyword |
| 5 | Avatar ≠ authentication | `user_id` is read from session, never from claim text |

## Two operating modes

### STANDALONE

```python
from matverse.cassandra_agent import CassandraAgent
agent = CassandraAgent(mode="standalone")
run = agent.chat("o que é MNB?")
# → uses local_interpret(), no network, no LLM, no key needed
```

### BASE44_REMOTE

```python
import os
os.environ["BASE44_API_KEY"] = "<from Base44 secret manager>"

from matverse.cassandra_agent import CassandraAgent
agent = CassandraAgent(mode="auto")  # auto-detects env
run = agent.chat("liste os receipts mais recentes", persist=True)
# → authenticates once, uses SessionToken + CapabilityToken
# → on failure, falls back to STANDALONE
```

## Rotation policy

When a `BASE44_API_KEY` is exposed (e.g., pasted in a public document,
logged in plaintext, sent in chat), it MUST be rotated immediately:

1. Rotate the key in the Base44 secret manager.
2. Restart any process that loaded the key.
3. Re-deploy with the new key in the secret manager.
4. Never commit the new key to git, env files, or shared docs.
5. Audit the GitHub repo with `git log -p -S BASE44_API_KEY` to confirm
   no plaintext key is in history.

The constitutional audit (2026-07-15) identified an exposed key in a
Base44 build attachment. That key is considered compromised and is being
rotated. The v3.8.2 code follows the rules above: the key is held only
during `__init__`, exchanged for a `SessionToken` immediately, and the
key is wiped from memory after the bootstrap.

## Versioning

- v3.8.2: added session + capability token model (api_key no longer
  sent on every call). All 36 Cassandra agent tests pass; 292/292
  organism tests pass.
- v3.8.1: lineage audit, no code changes.
- v3.8.0: GTHDL integration, formal MNB 5-tuple, Ω-score canonical.
- v3.7.0: full organism runner, 146/146 tests.
- v3.6.0: constitutional organs + physics, 116/116 tests.
- v3.0.0: initial 46/46 tests.

## Conftest

- Default Base44 app id: `6a2dd76b300afd3eb43293d7` (MatVerse URANO OSX).
- Default chat agent: `osx_chat`.
- Default session TTL: 3600s (1 hour).
- Default capability TTL: 600s (10 minutes).
