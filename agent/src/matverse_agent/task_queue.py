from __future__ import annotations

import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .config import Settings
from .runtime import AgentRuntime, RunResult


@dataclass(slots=True)
class TaskRecord:
    task_id: str
    goal: str
    status: str
    created_at: str
    updated_at: str
    run_id: str | None = None
    receipt: str | None = None
    result: str | None = None
    error: str | None = None

    def public(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "run_id": self.run_id,
            "receipt": self.receipt,
            "result": self.result,
            "error": self.error,
        }


class TaskQueue:
    def __init__(self, settings: Settings, workers: int = 3) -> None:
        self.settings = settings
        self.executor = ThreadPoolExecutor(max_workers=max(1, min(workers, 8)))
        self._lock = threading.RLock()
        self._records: dict[str, TaskRecord] = {}
        self._futures: dict[str, Future[RunResult]] = {}

    def submit(self, goal: str) -> TaskRecord:
        clean_goal = goal.strip()
        if not clean_goal:
            raise ValueError("Goal cannot be empty")
        now = datetime.now(timezone.utc).isoformat()
        task_id = uuid.uuid4().hex
        record = TaskRecord(
            task_id=task_id,
            goal=clean_goal,
            status="PENDING",
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._records[task_id] = record
            future = self.executor.submit(self._execute, task_id, clean_goal)
            self._futures[task_id] = future
        return record

    def get(self, task_id: str) -> TaskRecord:
        with self._lock:
            record = self._records.get(task_id)
            if record is None:
                raise KeyError(task_id)
            return record

    def list(self, limit: int = 100) -> list[TaskRecord]:
        with self._lock:
            records = list(self._records.values())
        return sorted(records, key=lambda item: item.created_at, reverse=True)[:limit]

    def _execute(self, task_id: str, goal: str) -> RunResult:
        self._update(task_id, status="RUNNING")
        try:
            result = AgentRuntime(self.settings).run(goal)
        except Exception as exc:
            self._update(
                task_id,
                status="FAILED",
                error=f"{type(exc).__name__}: {exc}",
            )
            raise
        self._update(
            task_id,
            status="COMPLETED" if result.status == "PASS" else "BLOCKED",
            run_id=result.run_id,
            receipt=str(result.receipt_path),
            result=result.final,
        )
        return result

    def _update(self, task_id: str, **changes: Any) -> None:
        with self._lock:
            record = self._records[task_id]
            for key, value in changes.items():
                setattr(record, key, value)
            record.updated_at = datetime.now(timezone.utc).isoformat()
