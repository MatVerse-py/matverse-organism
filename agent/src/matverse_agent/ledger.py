from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


GENESIS_HASH = "0" * 64


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class LedgerEvent:
    sequence: int
    run_id: str
    event_type: str
    payload: dict[str, Any]
    created_at: str
    previous_hash: str
    event_hash: str


class Ledger:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA foreign_keys=ON")
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    goal TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                );
                CREATE INDEX IF NOT EXISTS idx_events_run_sequence
                    ON events(run_id, sequence);
                """
            )

    def start_run(self, run_id: str, goal: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO runs(run_id, goal, status, created_at, updated_at)
                VALUES (?, ?, 'RUNNING', ?, ?)
                """,
                (run_id, goal, now, now),
            )

    def finish_run(self, run_id: str, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE runs SET status = ?, updated_at = ? WHERE run_id = ?",
                (status, now, run_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"Unknown run_id: {run_id}")

    def append(self, run_id: str, event_type: str, payload: dict[str, Any]) -> LedgerEvent:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connection() as connection:
            row = connection.execute(
                "SELECT event_hash FROM events ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
            previous_hash = GENESIS_HASH if row is None else str(row["event_hash"])
            material = {
                "run_id": run_id,
                "event_type": event_type,
                "payload": payload,
                "created_at": created_at,
                "previous_hash": previous_hash,
            }
            event_hash = hashlib.sha256(_canonical(material).encode("utf-8")).hexdigest()
            cursor = connection.execute(
                """
                INSERT INTO events(
                    run_id, event_type, payload_json, created_at, previous_hash, event_hash
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    event_type,
                    _canonical(payload),
                    created_at,
                    previous_hash,
                    event_hash,
                ),
            )
            sequence = int(cursor.lastrowid)
        return LedgerEvent(
            sequence=sequence,
            run_id=run_id,
            event_type=event_type,
            payload=payload,
            created_at=created_at,
            previous_hash=previous_hash,
            event_hash=event_hash,
        )

    def events_for_run(self, run_id: str) -> list[LedgerEvent]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM events WHERE run_id = ? ORDER BY sequence",
                (run_id,),
            ).fetchall()
        return [
            LedgerEvent(
                sequence=int(row["sequence"]),
                run_id=str(row["run_id"]),
                event_type=str(row["event_type"]),
                payload=json.loads(str(row["payload_json"])),
                created_at=str(row["created_at"]),
                previous_hash=str(row["previous_hash"]),
                event_hash=str(row["event_hash"]),
            )
            for row in rows
        ]

    def verify(self) -> tuple[bool, str]:
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM events ORDER BY sequence").fetchall()
        expected_previous = GENESIS_HASH
        for row in rows:
            payload = json.loads(str(row["payload_json"]))
            material = {
                "run_id": str(row["run_id"]),
                "event_type": str(row["event_type"]),
                "payload": payload,
                "created_at": str(row["created_at"]),
                "previous_hash": str(row["previous_hash"]),
            }
            expected_hash = hashlib.sha256(
                _canonical(material).encode("utf-8")
            ).hexdigest()
            if str(row["previous_hash"]) != expected_previous:
                return False, f"Broken previous_hash at sequence {row['sequence']}"
            if str(row["event_hash"]) != expected_hash:
                return False, f"Invalid event_hash at sequence {row['sequence']}"
            expected_previous = expected_hash
        return True, f"PASS: {len(rows)} events verified"
