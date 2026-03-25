#!/usr/bin/env python3
"""Continuous guardian process for MatVerse organism."""

from __future__ import annotations

import argparse
import json
import logging
import signal
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests

from guardian_config import GuardianConfig
from organism_client import OrganismClient


class Guardian:
    def __init__(self, config: GuardianConfig):
        self.config = config
        self.client = OrganismClient(config.base_url)
        self.running = True
        self.diagnostics: List[Dict[str, Any]] = []
        self._setup_logging()

    def _setup_logging(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.FileHandler(self.config.log_path), logging.StreamHandler()],
        )

    def _status(self, state: Dict[str, Any]) -> str:
        psi = float(state.get("psi", 0.0))
        cells = int(state.get("cells", 0))
        if cells <= self.config.critical_cells:
            return "critical"
        if psi >= self.config.thriving_psi:
            return "thriving"
        if psi >= self.config.healthy_psi:
            return "healthy"
        if psi >= self.config.stressed_psi:
            return "stressed"
        return "critical"

    def _record(self, event_type: str, status: str, metric: float, action: str) -> None:
        self.diagnostics.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "status": status,
                "metric": metric,
                "action_taken": action,
            }
        )

    def _persist(self) -> None:
        Path(self.config.diagnostics_path).write_text(
            json.dumps(self.diagnostics, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _act(self, status: str) -> None:
        if status == "thriving":
            self.client.procreate(self.config.test_energy)
            self._record("perturbation", "applied", self.config.test_energy, f"procreate({self.config.test_energy})")
            logging.info("⚡ Thriving: test perturbation applied (energy=%s)", self.config.test_energy)
        elif status == "critical":
            for _ in range(3):
                self.client.procreate(self.config.repair_energy)
            self._record("repair", "applied", self.config.repair_energy, "3x procreate repair")
            logging.warning("🛡️ Critical: recovery cells injected")
        elif status == "stressed":
            self._record("monitor", "stressed", 0.0, "observe only")
            logging.info("⚠️ Stressed: monitoring recovery")

    def run(self, duration: int | None = None) -> None:
        start = time.time()
        logging.info("🛡️ Guardian started for %s", self.config.base_url)
        while self.running:
            if duration is not None and time.time() - start >= duration:
                break
            try:
                state = self.client.state()
                status = self._status(state)
                psi = float(state.get("psi", 0.0))
                cells = int(state.get("cells", 0))
                logging.info("🔍 status=%s psi=%.3f cells=%d", status, psi, cells)
                self._record("health_check", status, psi, "assessed")
                self._act(status)
                self._persist()
            except requests.RequestException as exc:
                logging.error("Connection issue: %s", exc)
                self._record("connection", "error", 0.0, str(exc))
                self._persist()
            time.sleep(self.config.check_interval_seconds)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="MatVerse Guardian")
    p.add_argument("--base-url", default="http://localhost:8765")
    p.add_argument("--check-interval", type=int, default=10)
    p.add_argument("--duration", type=int)
    p.add_argument("--diagnostic-file", default="diagnostics.json")
    p.add_argument("--log-file", default="guardian.log")
    p.add_argument("--summary", action="store_true")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    cfg = GuardianConfig(
        base_url=args.base_url,
        check_interval_seconds=args.check_interval,
        diagnostics_path=args.diagnostic_file,
        log_path=args.log_file,
    )
    if args.summary:
        print(json.dumps(asdict(cfg), indent=2, ensure_ascii=False))
        return 0

    guardian = Guardian(cfg)

    def _stop(_sig: int, _frame: Any) -> None:
        guardian.running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    guardian.run(args.duration)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
