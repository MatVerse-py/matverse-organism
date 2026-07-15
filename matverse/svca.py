"""
matverse.svca
=============

SVCA — S Vídeo-Cápsula de Auditoria, but more precisely:
"S Vídeo-Cápsula de Aplicação".

A SVCA is a proof capsule that bundles EVERYTHING needed to verify
that a transmutation was real, in what conditions, and whether it can
be reproduced:

  - input       (the state before the mutation)
  - config      (the UMJAMSpec)
  - environment (Python version, hostname, library fingerprint, ...)
  - execution   (capability id, seed, status, duration, errors)
  - result      (UMJAMResult.output, refusal_reason if any)
  - metrics     (caller-defined; e.g. mean, ci, regenerative_ratio, ...)
  - hashes      (input_hash, output_hash, receipt_hash, ledger_tip)
  - receipt     (a copy of the canonical receipt)
  - replay      (the seed, the capability id, the function name — everything
                 another operator needs to run the same transmutation)

The SVCA is the canonical object the Closure Compiler uses to render
the four projections: Paper, Code, Execution, Canonization.

The SVCA is intentionally a plain dataclass. It can be JSON-serialized,
hash-signed, and replayed.
"""
from __future__ import annotations
import hashlib
import json
import os
import platform
import socket
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from .umjam import UMJAMSpec, UMJAMResult


@dataclass
class SVCA:
    """Proof capsule of a transmutation.

    Constructed via `SVCA.from_transmutation(spec, result, metrics=...)`.
    The capsule is the input to the Closure Compiler and the Publication
    Layer.
    """

    svca_id: str
    operation_id: str
    capability_id: str

    # input
    input_state: Dict[str, Any] = field(default_factory=dict)
    input_hash: str = ""

    # config
    spec: Dict[str, Any] = field(default_factory=dict)

    # environment
    environment: Dict[str, Any] = field(default_factory=dict)

    # execution
    execution: Dict[str, Any] = field(default_factory=dict)

    # result
    output: Dict[str, Any] = field(default_factory=dict)
    status: str = "PASS"
    refusal_reason: str = ""

    # metrics
    metrics: Dict[str, Any] = field(default_factory=dict)

    # hashes
    hashes: Dict[str, str] = field(default_factory=dict)

    # receipt
    receipt: Dict[str, Any] = field(default_factory=dict)

    # replay conditions
    replay: Dict[str, Any] = field(default_factory=dict)

    timestamp: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def canonical_hash(self) -> str:
        """Stable SHA-256 of the SVCA's content. Used for canonization."""
        payload = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()

    @classmethod
    def from_transmutation(
        cls,
        spec: UMJAMSpec,
        result: UMJAMResult,
        *,
        metrics: Optional[Dict[str, Any]] = None,
        caller_provenance: Optional[Dict[str, Any]] = None,
    ) -> "SVCA":
        env = _capture_environment(caller_provenance or {})
        execution = {
            "capability_id": spec.capability_id,
            "operation_id": spec.operation_id,
            "seed": spec.seed,
            "fail_closed": spec.fail_closed,
            "started_at": result.timestamp,
            "duration_s": None,  # populated by caller if available
        }
        input_hash = hashlib.sha256(
            json.dumps({"inputs": spec.inputs}, sort_keys=True, default=str).encode()
        ).hexdigest()
        output_hash = hashlib.sha256(
            json.dumps(result.output, sort_keys=True, default=str).encode()
        ).hexdigest()
        hashes = {
            "input_hash": input_hash,
            "output_hash": output_hash,
            "receipt_hash": result.receipt_hash,
        }
        replay = {
            "capability_id": spec.capability_id,
            "seed": spec.seed,
            "inputs": spec.inputs,
            "constraints": spec.constraints,
            "limits": spec.limits,
            "instructions": (
                f"Run `matverse.umjam.transmute(UMJAMSpec(...), <state>)` with "
                f"the same capability, seed, and inputs."
            ),
        }
        return cls(
            svca_id=f"SVCA-{int(time.time())}-{spec.operation_id}",
            operation_id=spec.operation_id,
            capability_id=spec.capability_id,
            input_state=spec.inputs,
            input_hash=input_hash,
            spec=spec.to_dict(),
            environment=env,
            execution=execution,
            output=result.output,
            status=result.status,
            refusal_reason=result.refusal_reason,
            metrics=metrics or {},
            hashes=hashes,
            receipt=result.ledger_entry,
            replay=replay,
            timestamp=result.timestamp,
        )

    def is_reproducible(self) -> bool:
        """A SVCA is reproducible iff it has a seed, a capability, and inputs."""
        return all([
            self.execution.get("seed") is not None,
            self.execution.get("capability_id"),
            isinstance(self.replay.get("inputs"), dict),
        ])


def _capture_environment(extra: Dict[str, Any]) -> Dict[str, Any]:
    env = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
        "cwd": os.getcwd(),
        "pid": os.getpid(),
        "ts": int(time.time()),
    }
    env.update(extra)
    return env
