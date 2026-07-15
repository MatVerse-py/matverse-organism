"""
matverse.replay
===============

Independent replay verification.

A closure's `replay_status` advances from:

  LOCAL_REPLAYED
  -> INDEPENDENT_REPLAYED          (different operator or machine)
  -> WITNESSED_EXTERNAL            (anchor on external witness, e.g. blockchain)

The Replayer takes an SVCA, re-runs the capability with the recorded
seed and inputs in a fresh environment, and produces a replay_report
that the Closure Compiler can use to upgrade the replay_status.

Replayer is intentionally simple: it re-invokes the capability in
the live registry, with the recorded seed. It cannot re-create a
witness; that requires a separate human or external system.
"""
from __future__ import annotations
import hashlib
import json
import os
import platform
import socket
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .svca import SVCA
from .umjam import UMJAM, UMJAMSpec


@dataclass
class ReplayReport:
    svca_id: str
    operation_id: str
    capability_id: str
    seed_used: int
    inputs_used: Dict[str, Any]
    local_env: Dict[str, Any]
    output_hash: str
    expected_output_hash: str
    matches: bool
    delta_summary: Dict[str, Any] = field(default_factory=dict)
    ts: int = 0
    independent: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "svca_id": self.svca_id,
            "operation_id": self.operation_id,
            "capability_id": self.capability_id,
            "seed_used": self.seed_used,
            "inputs_used": self.inputs_used,
            "local_env": self.local_env,
            "output_hash": self.output_hash,
            "expected_output_hash": self.expected_output_hash,
            "matches": self.matches,
            "delta_summary": self.delta_summary,
            "ts": self.ts,
            "independent": self.independent,
        }


class Replayer:
    """Re-runs a transmutation from its SVCA and compares the result."""

    def __init__(self, umjam: UMJAM) -> None:
        self.umjam = umjam

    def replay(self, svca: SVCA, *,
               independent: bool = False) -> ReplayReport:
        spec_dict = svca.spec
        spec = UMJAMSpec(
            operation_id=spec_dict.get("operation_id", svca.operation_id),
            capability_id=spec_dict.get("capability_id", svca.capability_id),
            inputs=spec_dict.get("inputs", {}),
            constraints=spec_dict.get("constraints", []),
            limits=spec_dict.get("limits", {}),
            fail_closed=spec_dict.get("fail_closed", True),
            subject=spec_dict.get("subject", ""),
            consent=spec_dict.get("consent", "implicit"),
            key=spec_dict.get("key", ""),
            purpose=spec_dict.get("purpose", ""),
            seed=spec_dict.get("seed", 0),
            timestamp=0,
        )
        # Reconstruct state from inputs
        state = spec.inputs if isinstance(spec.inputs, dict) else {}
        result = self.umjam.transmute(spec, state)
        local_output_hash = hashlib.sha256(
            json.dumps(result.output, sort_keys=True, default=str).encode()
        ).hexdigest()
        expected = svca.hashes.get("output_hash", "")
        matches = local_output_hash == expected

        delta = {}
        if not matches:
            # Compute a tiny diff for the report
            try:
                exp = json.loads(json.dumps(svca.output))
                got = json.loads(json.dumps(result.output))
                keys = set(exp.keys()) | set(got.keys())
                for k in keys:
                    if exp.get(k) != got.get(k):
                        delta[k] = {"expected": exp.get(k),
                                    "got": got.get(k)}
            except Exception:
                delta = {"error": "could not diff outputs"}

        return ReplayReport(
            svca_id=svca.svca_id,
            operation_id=svca.operation_id,
            capability_id=svca.capability_id,
            seed_used=spec.seed,
            inputs_used=spec.inputs,
            local_env={
                "hostname": socket.gethostname(),
                "platform": platform.platform(),
                "python": __import__("sys").version,
                "cwd": os.getcwd(),
            },
            output_hash=local_output_hash,
            expected_output_hash=expected,
            matches=matches,
            delta_summary=delta,
            ts=int(time.time()),
            independent=independent,
        )
