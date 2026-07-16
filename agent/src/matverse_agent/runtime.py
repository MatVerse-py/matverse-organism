from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .config import Settings
from .ledger import Ledger
from .ollama_client import OllamaClient
from .tools import ApprovalCallback, ToolRegistry


SYSTEM_PROMPT = """You are MatVerse Agent Local, an autonomous engineering and research agent.

Operating contract:
1. Inspect the workspace before claiming anything about it.
2. Convert the goal into concrete steps internally, then execute with tools.
3. Prefer reversible changes, small diffs and existing project conventions.
4. Run relevant tests, linters or validation before declaring completion.
5. Never claim a file, test, build, publication or external action exists unless a tool result supports it.
6. When a tool fails, diagnose and attempt a bounded correction.
7. Do not invent metrics. Use NOT_MEASURED or NOT_COMPUTABLE when data is absent.
8. Preserve user files and lineage. Do not delete or overwrite without necessity.
9. Finish with a concise report: result, changed files, verification, residual risks and status.
10. You are in a multi-turn tool loop. Continue calling tools until the goal is complete or blocked.
"""


@dataclass(frozen=True, slots=True)
class RunResult:
    run_id: str
    status: str
    final: str
    run_dir: Path
    receipt_path: Path
    steps: int
    tool_calls: int


class AgentRuntime:
    def __init__(
        self,
        settings: Settings,
        approval_callback: ApprovalCallback | None = None,
    ) -> None:
        self.settings = settings
        self.ledger = Ledger(settings.database_path)
        self.client = OllamaClient(settings.ollama_url, settings.model)
        self.approval_callback = approval_callback

    def run(self, goal: str) -> RunResult:
        clean_goal = goal.strip()
        if not clean_goal:
            raise ValueError("Goal cannot be empty")

        run_id = uuid.uuid4().hex
        run_dir = self.settings.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        started_at = datetime.now(timezone.utc)
        self.ledger.start_run(run_id, clean_goal)
        self.ledger.append(
            run_id,
            "RUN_STARTED",
            {
                "goal": clean_goal,
                "workspace": str(self.settings.workspace),
                "model": self.settings.model,
                "approval_mode": self.settings.approval_mode,
                "network_enabled": self.settings.network_enabled,
            },
        )
        request = {
            "run_id": run_id,
            "goal": clean_goal,
            "started_at": started_at.isoformat(),
            "settings": {
                "model": self.settings.model,
                "max_steps": self.settings.max_steps,
                "approval_mode": self.settings.approval_mode,
                "network_enabled": self.settings.network_enabled,
            },
        }
        self._write_json(run_dir / "request.json", request)

        registry = ToolRegistry(
            self.settings,
            self.ledger,
            run_id,
            approval_callback=self.approval_callback,
        )
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": clean_goal},
        ]
        final = ""
        status = "BLOCK"
        tool_count = 0
        step_count = 0
        error: str | None = None

        try:
            for step_count in range(1, self.settings.max_steps + 1):
                response = self.client.chat(messages, registry.schemas)
                assistant = self._sanitized_assistant_message(response)
                messages.append(assistant)
                tool_calls = assistant.get("tool_calls", [])
                self.ledger.append(
                    run_id,
                    "MODEL_RESPONSE",
                    {
                        "step": step_count,
                        "content_sha256": hashlib.sha256(
                            str(assistant.get("content", "")).encode("utf-8")
                        ).hexdigest(),
                        "tool_names": [
                            call.get("function", {}).get("name")
                            for call in tool_calls
                            if isinstance(call, dict)
                        ],
                    },
                )

                if not tool_calls:
                    final = str(assistant.get("content", "")).strip()
                    status = "PASS" if final else "HOLD"
                    break

                for call in tool_calls:
                    if not isinstance(call, dict):
                        continue
                    function = call.get("function", {})
                    name = str(function.get("name", ""))
                    arguments = self._arguments(function.get("arguments", {}))
                    self.ledger.append(
                        run_id,
                        "TOOL_CALL",
                        {
                            "step": step_count,
                            "tool": name,
                            "arguments": registry.policy.redact(arguments),
                        },
                    )
                    result = registry.execute(name, arguments)
                    tool_count += 1
                    messages.append(
                        {
                            "role": "tool",
                            "tool_name": name,
                            "content": json.dumps(result, ensure_ascii=False, sort_keys=True),
                        }
                    )
            else:
                final = f"Maximum step limit reached: {self.settings.max_steps}"
                status = "BLOCK"
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            final = error
            status = "BLOCK"
            self.ledger.append(run_id, "RUN_ERROR", {"error": error})

        finished_at = datetime.now(timezone.utc)
        self.ledger.append(
            run_id,
            "RUN_FINISHED",
            {
                "status": status,
                "steps": step_count,
                "tool_calls": tool_count,
                "duration_seconds": (finished_at - started_at).total_seconds(),
                "error": error,
            },
        )
        self.ledger.finish_run(run_id, status)

        public_messages = [self._public_message(message) for message in messages]
        self._write_json(run_dir / "messages.json", public_messages)
        (run_dir / "result.md").write_text(final + "\n", encoding="utf-8")

        changed_files = self._changed_files(started_at)
        events = self.ledger.events_for_run(run_id)
        receipt = {
            "run_id": run_id,
            "status": status,
            "goal_sha256": hashlib.sha256(clean_goal.encode("utf-8")).hexdigest(),
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_seconds": (finished_at - started_at).total_seconds(),
            "steps": step_count,
            "tool_calls": tool_count,
            "model": self.settings.model,
            "workspace": str(self.settings.workspace),
            "changed_files": changed_files,
            "ledger_events": [
                {"sequence": event.sequence, "event_hash": event.event_hash}
                for event in events
            ],
            "result_sha256": hashlib.sha256(final.encode("utf-8")).hexdigest(),
        }
        receipt_path = run_dir / "receipt.json"
        self._write_json(receipt_path, receipt)
        return RunResult(
            run_id=run_id,
            status=status,
            final=final,
            run_dir=run_dir,
            receipt_path=receipt_path,
            steps=step_count,
            tool_calls=tool_count,
        )

    @staticmethod
    def run_parallel(
        settings: Settings,
        goals: list[str],
        workers: int = 3,
        approval_callback: ApprovalCallback | None = None,
    ) -> list[RunResult]:
        if not goals:
            return []
        bounded_workers = max(1, min(workers, len(goals), 8))
        results: list[RunResult] = []
        with ThreadPoolExecutor(max_workers=bounded_workers) as executor:
            futures = {
                executor.submit(AgentRuntime(settings, approval_callback).run, goal): goal
                for goal in goals
            }
            for future in as_completed(futures):
                results.append(future.result())
        return sorted(results, key=lambda item: item.run_id)

    @staticmethod
    def _arguments(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        raise ValueError("Tool arguments must be a JSON object")

    @staticmethod
    def _sanitized_assistant_message(message: dict[str, Any]) -> dict[str, Any]:
        sanitized: dict[str, Any] = {
            "role": "assistant",
            "content": str(message.get("content", "")),
        }
        tool_calls = message.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            sanitized["tool_calls"] = tool_calls
        return sanitized

    @staticmethod
    def _public_message(message: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in message.items() if key != "thinking"}

    def _changed_files(self, started_at: datetime) -> list[dict[str, Any]]:
        git_rows = self._git_changed_files()
        if git_rows is not None:
            return git_rows
        rows: list[dict[str, Any]] = []
        timestamp = started_at.timestamp()
        for path in self.settings.workspace.rglob("*"):
            if not path.is_file() or any(part in {".git", ".matverse"} for part in path.parts):
                continue
            if path.stat().st_mtime < timestamp:
                continue
            rows.append(self._file_receipt(path, "modified"))
        return rows[:2000]

    def _git_changed_files(self) -> list[dict[str, Any]] | None:
        if not (self.settings.workspace / ".git").exists():
            return None
        process = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z"],
            cwd=self.settings.workspace,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if process.returncode != 0:
            return None
        entries = process.stdout.decode("utf-8", errors="replace").split("\x00")
        rows: list[dict[str, Any]] = []
        for entry in entries:
            if len(entry) < 4:
                continue
            status = entry[:2]
            relative = entry[3:]
            path = self.settings.workspace / relative
            if path.is_file():
                rows.append(self._file_receipt(path, status))
            else:
                rows.append({"path": relative, "status": status, "missing": True})
        return rows

    def _file_receipt(self, path: Path, status: str) -> dict[str, Any]:
        content = path.read_bytes()
        return {
            "path": path.relative_to(self.settings.workspace).as_posix(),
            "status": status,
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }

    @staticmethod
    def _write_json(path: Path, value: Any) -> None:
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
