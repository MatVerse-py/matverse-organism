# Cassandra ↔ Base44 integration guide

This document records how the local Cassandra agent
(`matverse.cassandra_agent`) connects to the Base44 app
**MatVerse URANO OSX** (app id `6a2dd76b300afd3eb43293d7`).

## Two modes

| Mode | What it does | Requires |
|------|-------------|----------|
| `STANDALONE` | Local rule-based interpreter, no network | nothing |
| `BASE44_REMOTE` | Uses Base44 chat agent API (`/apps/{id}/agents/...`) | `BASE44_API_KEY` env var |
| `HYBRID` | Local interpreter + Base44 entity persistence | `BASE44_API_KEY` env var |

The mode is auto-detected from the env var if you pass `mode="auto"`
(the default).

## Quick start

### 1. Set the API key

```bash
export BASE44_API_KEY="<your base44 api key>"
# The key is read from the env, never stored on disk.
```

You can find the key in Base44:
**Dashboard → Settings → API keys**. The default `osx_chat` agent is
already created in the MatVerse URANO OSX app.

### 2. Use the agent from Python

```python
from matverse import CassandraAgent

# Auto mode: uses Base44 if BASE44_API_KEY is set, else standalone
agent = CassandraAgent()
print(agent.mode)  # "base44" or "standalone"

# Single chat
run = agent.chat("o que é o Ω-Score?")
print(run.cassandra_response)
print(run.gate_status)         # PASS | HOLD | ESCALATE | DENY
print(run.epistemic_classification)  # OBS | INF | HYP | ...

# Persist the run to Base44 (only works in base44 mode)
run = agent.chat("publique agora no Zenodo", persist=True)
print(run.gate_status)  # ESCALATE — fail-closed
```

### 3. Use the agent from the CLI

```bash
# Standalone
python -m matverse cassandra chat "o que é o MNB?"

# Base44 (requires BASE44_API_KEY)
export BASE44_API_KEY="..."
python -m matverse cassandra chat "liste as intents mais recentes" --persist
```

## Base44 entities that Cassandra touches

| Entity | Operation | When |
|--------|-----------|------|
| `CassandraRun` | create | every chat (if `persist=True`) |
| `RuntimeIntent` | read | when chat mentions "intenção" or "intent" |
| `RuntimeReceipt` | read | when chat mentions "receipt" or "receipts" |
| `RuntimeFinding` | read | when chat mentions "finding" or "findings" |
| `CassandraProfile` | read | at agent init (operational parameters) |

The agent has read/create permission scoped to these entities.
The agent never deletes, never updates, never executes external
actions, never publishes, never signs.

## Constitutional position

The agent enforces **5 hard limits**:

1. **No external action** — never calls a non-listed API, never
   publishes, never signs.
2. **Evidence before claim** — OBS claims must point to a `source_id`.
3. **Determinism** — the same `policy_version` + the same input
   must produce the same output.
4. **Fail-closed** — when in doubt, ESCALATE.
5. **Avatar ≠ authentication** — the user is identified by
   `user_id` from the Base44 session, not by avatar/role claim.

These limits are encoded in the system prompt
(`matverse.cassandra_prompt.CASSANDRA_SYSTEM_PROMPT`) and are
immutable from the user side. The `system_prompt_text()` method
exposes the full prompt for audit.

## Endpoints used

From the Base44 docs (visible in the Base44 dashboard):

```
GET  /entities/SGIMetric                  — list SGI metrics
GET  /entities/RuntimeIntent              — list runtime intents
POST /entities/CassandraRun               — log a Cassandra run
GET  /apps/{app_id}/agents/conversations  — list conversations
POST /apps/{app_id}/agents/conversations  — create a conversation
POST /apps/{app_id}/agents/conversations/{cid}/messages  — send a message
```

`app_id` = `6a2dd76b300afd3eb43293d7` by default.

## Local fallback (no API key)

If `BASE44_API_KEY` is not set, the agent operates in `STANDALONE`
mode. The local interpreter (`cassandra_base44.local_interpret`)
implements the same 5 hard limits via pattern matching against the
user input. The behavior is deterministic and reproducible — useful
for tests, CI, and offline demos.

## What v3.8.2 ships (this PR)

- `matverse/cassandra_prompt.py` — the constitutional system prompt
  (4 layers: ROLE / SCOPE / ADMISSIBILITY / EPITEMIC + CANONICAL_CORPUS)
- `matverse/cassandra_base44.py` — `Base44Client`, `CassandraAgent`,
  `CassandraRun`, `local_interpret`
- `matverse/cassandra_agent.py` — facade re-exports
- `tests/test_cassandra_agent.py` — 30+ tests
- CLI command `hypo cassandra chat` (added to `matverse/cli.py`)
- This document

## What v3.8.2 does NOT ship

- A real LLM integration (the agent is deterministic; it can be
  wrapped around an LLM later, but v3.8.2 ships without one)
- A real-time streaming endpoint (only request/response)
- Multimodal input (text only)
- Persistent agent memory across runs (the MMNB lineage is the
  memory; the agent reads it but does not write to it directly)
- The 3 HOLD skills: TACE, H-Axis, impact_briefing (per
  `references/cassandra_model.md`)

## Verification

```bash
$ python -m unittest discover -s tests -k cassandra
Ran 30 tests in 0.4s
OK

$ python -c "
from matverse import CassandraAgent
a = CassandraAgent()
print(a.mode)
r = a.chat('o que é o Ω-Score?')
print(r.epistemic_classification, r.gate_status)
"
standalone
OBS PASS
```
