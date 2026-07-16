# MatVerse Agent Local — Design Record

## Goal

Provide a no-mandatory-API-cost autonomous local agent with the functional classes users associate with AgentGPT, Manus and Codex: planning, long-running tasks, code changes, research, browser and shell tools, files, parallel agents, skills, connectors and artifact generation.

This is functional equivalence, not a copy of proprietary models, private infrastructure or branding.

## Source decisions

### Codex Cloud

Patterns adopted:

- goal-oriented engineering tasks;
- Git worktrees for parallel isolation;
- project instructions through `AGENTS.md`;
- skills loaded on demand;
- shell, review, test and repair loops;
- non-interactive execution mode;
- MCP integration;
- task status and reviewable changed-file receipts.

Local implementation:

- `AgentRuntime.run_parallel()` creates isolated worktrees;
- `SkillLibrary` loads `AGENTS.md` and Markdown skills;
- `TaskQueue` provides asynchronous task IDs;
- `ToolRegistry` provides filesystem, terminal, Git, research and artifacts;
- `receipt.json` and the SQLite hash ledger provide review evidence.

### GPAI problems

The public page exposes a STEM problem surface but not an inspectable execution protocol. The useful abstraction is retained as `ProblemContract`:

- objective;
- success criteria;
- constraints;
- deliverables;
- verification.

No proprietary GPAI implementation or content is copied.

### GPT Cassandra Pilot

The repository is based on the discontinued GPT Pilot architecture. Adopted:

- specification writer;
- architect;
- tech lead/implementer;
- reviewer;
- debugger;
- technical writer;
- incremental app construction rather than one-shot code dumps.

Not adopted:

- mandatory paid LLM providers;
- legacy telemetry;
- destructive rewind behavior;
- numerical quorum gates that accept unmeasured Omega/Psi/CVaR inputs;
- a later simplified quorum implementation that counts threshold-passing nodes without requiring agreement on the same receipt and Merkle root.

### MatVerse skills repository

The current repository README identifies itself as a scaffold. Therefore it is not imported as a trusted ready-made library. The runtime instead implements a generic local Markdown skill loader. The repository can be cloned or copied into `workspace/skills/` after individual skills are reviewed.

### KiloMan

KiloMan is a Next.js game interface. Its reusable contribution is interaction style: full-screen command surface, visible state and event-driven UI. The agent command center uses the same high-level interaction principle but does not couple the runtime to the game code or React release candidates.

## Architecture

```text
Goal
  -> ProblemContract
  -> Skill selection
  -> Role-aware system prompt
  -> Ollama tool-calling loop
  -> Policy gate
  -> Files / shell / Git / browser / SearXNG / artifact tools
  -> optional outbound MCP connector gateway
  -> verification
  -> SQLite hash ledger + run receipt
```

## Trust states

- `NARRATED`: the model said it happened.
- `OBSERVED`: a tool or file records it.
- `REPRODUCED`: validation reran successfully.
- `BLOCK`: a required gate failed.
- `HOLD`: more input, approval or dependency is required.

Only `OBSERVED` and `REPRODUCED` support completion claims.

## Autonomy

`MATVERSE_APPROVAL_MODE=never` enables autonomous execution of commands allowed by policy. It does not disable constitutional blocks. Global destructive commands, privilege escalation, metadata endpoints, traversal outside the workspace and pipe-to-shell installers remain blocked.

This is deliberate: equivalent capability does not require equivalent blast radius.

## Free operation

The default path uses:

- Ollama for local inference;
- SQLite for memory and ledger;
- SearXNG for local metasearch;
- Playwright for browser automation;
- Git worktrees for parallel agents;
- MCP for connectors;
- Pillow, python-pptx and FFmpeg for artifacts.

Internet access, model downloads, hardware and electricity can still have external cost. No API subscription is required for the default runtime.
