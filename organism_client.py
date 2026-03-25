#!/usr/bin/env python3
"""CLI client for MatVerse organism APIs."""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Dict

import requests


class OrganismClient:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def state(self) -> Dict[str, Any]:
        r = requests.get(self._url("/api/organism/state"), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def cells(self) -> list[Dict[str, Any]]:
        r = requests.get(self._url("/api/cells"), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def procreate(self, energy: float = 1.0) -> Dict[str, Any]:
        r = requests.post(self._url("/api/cell/procreate"), json={"energy": energy}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def stream(self, seconds: int = 10) -> None:
        end = time.time() + seconds
        with requests.get(self._url("/api/organism/stream"), timeout=self.timeout, stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=True):
                if time.time() >= end:
                    break
                if not line or not line.startswith("data: "):
                    continue
                payload = line[6:].strip()
                try:
                    print(json.dumps(json.loads(payload), ensure_ascii=False))
                except json.JSONDecodeError:
                    print(payload)

    def measure_response(self, perturb_energy: float = 0.5, observation_seconds: int = 10) -> Dict[str, Any]:
        before = self.state()
        self.procreate(energy=perturb_energy)
        time.sleep(max(1, observation_seconds))
        after = self.state()
        return {
            "before": before,
            "after": after,
            "delta_cells": after.get("cells", 0) - before.get("cells", 0),
            "delta_psi": after.get("psi", 0.0) - before.get("psi", 0.0),
        }



def main() -> int:
    parser = argparse.ArgumentParser(description="MatVerse organism client")
    parser.add_argument("--base-url", default="http://localhost:8765")
    parser.add_argument("--state", action="store_true")
    parser.add_argument("--cells", action="store_true")
    parser.add_argument("--procreate", type=float, metavar="ENERGY")
    parser.add_argument("--stream", type=int, metavar="SECONDS")
    parser.add_argument("--measure-response", type=float, metavar="ENERGY")
    parser.add_argument("--observation-seconds", type=int, default=10)

    args = parser.parse_args()
    client = OrganismClient(args.base_url)

    try:
        if args.state:
            print(json.dumps(client.state(), indent=2, ensure_ascii=False))
            return 0
        if args.cells:
            print(json.dumps(client.cells(), indent=2, ensure_ascii=False))
            return 0
        if args.procreate is not None:
            print(json.dumps(client.procreate(args.procreate), indent=2, ensure_ascii=False))
            return 0
        if args.stream is not None:
            client.stream(args.stream)
            return 0
        if args.measure_response is not None:
            result = client.measure_response(args.measure_response, args.observation_seconds)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

        parser.print_help()
        return 0
    except requests.RequestException as exc:
        print(f"request failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
