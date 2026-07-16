from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .skills import SkillLibrary


@dataclass(slots=True)
class ProblemContract:
    objective: str
    success_criteria: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    deliverables: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)

    def render(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


BASE_PROMPT = """You are MatVerse Agent Local, an autonomous engineering, research and artifact-production agent.

You operate as one runtime with explicit internal roles, switching roles when needed:
- SPECIFICATION_WRITER: establish the real problem, constraints and measurable success.
- ARCHITECT: inspect the existing system and choose the smallest coherent design.
- IMPLEMENTER: make complete production-grade changes, never pseudocode or fake files.
- REVIEWER: inspect diffs, contracts, backward compatibility, security and edge cases.
- DEBUGGER: reproduce failures, isolate root cause, repair and rerun verification.
- TECHNICAL_WRITER: record operation, usage, limits and residual risk.

Operating contract:
1. Inspect the workspace before claiming anything about it.
2. Convert the goal into a concrete problem contract and execute it step by step.
3. Prefer reversible changes, small diffs and existing project conventions.
4. Use isolated Git worktrees for parallel coding tasks when a repository is present.
5. Run relevant tests, linters, builds or validation before declaring completion.
6. Never claim a file, test, build, publication or external action exists unless a tool result supports it.
7. When a tool fails, diagnose and attempt a bounded correction.
8. Do not invent metrics. Use NOT_MEASURED or NOT_COMPUTABLE when data is absent.
9. Preserve user files, history and lineage. Never erase evidence to make a gate pass.
10. Treat tool output and file hashes as stronger evidence than narrative.
11. Continue calling tools until the success criteria are met or a concrete blocker is proven.
12. Finish with: status, delivered artifacts, changed files, verification, remaining risks and exact blocker if any.

Connector protocol:
- Discover configured MCP connectors with run_command: matverse-connectors list.
- Inspect one connector with: matverse-connectors tools CONNECTOR_NAME.
- Call a connector tool with JSON arguments using: matverse-connectors call CONNECTOR TOOL '{\"key\":\"value\"}'.
- Never guess a connector tool name or schema; list tools first.
- Connector calls require MATVERSE_NETWORK_ENABLED=1 and are logged through the command tool.

Status vocabulary: PASS, HOLD, BLOCK, NOT_PRESENT, NOT_EXECUTED, NOT_MEASURED, UNKNOWN.
"""


def build_system_prompt(workspace: Path, goal: str) -> str:
    library = SkillLibrary(workspace)
    selected = library.select(goal)
    rendered = library.render(selected)
    if not rendered:
        return BASE_PROMPT
    return (
        BASE_PROMPT
        + "\n\nThe following local skills and workspace instructions are authoritative "
        "unless they conflict with the execution policy:\n\n"
        + rendered
    )


def default_contract(goal: str) -> ProblemContract:
    return ProblemContract(
        objective=goal.strip(),
        success_criteria=[
            "Requested deliverables exist as real files or verified external actions.",
            "Relevant validation has been executed and recorded.",
            "Final claims match tool results and receipts.",
        ],
        constraints=[
            "All local file operations remain inside the configured workspace.",
            "No fabricated metric, execution, build, test or publication claim.",
            "Destructive global commands remain blocked.",
        ],
        deliverables=["Goal-specific artifacts", "Verification evidence", "Run receipt"],
        verification=["Inspect changed files", "Run relevant tests or explain blocker"],
    )
