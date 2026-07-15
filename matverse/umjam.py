"""
matverse.umjam
==============

UMJAM — Universal MatVerse Joint of Admissible Mutation.

UMJAM is the capability of *governed transmutation*. It takes a
structured operation already validated by the COG and applies it to
produce a new state, a receipt, and a ledger entry.

UMJAM is NOT a general executor. It is the explicit, contract-bound
realization of the COG's chosen capability. Its admissibility belongs
to the Gate; its identity belongs to the MMNB; its proof belongs to
the SVCA.

UMJAM receives a UMJAMSpec and produces a UMJAMResult. The two are
minimal and pure-Python-stdlib.

Canonical signature (per the corpus):

    UMJAM(S, P, C) -> (S', R, L)

where:
    S = state (input, payload, domain, schema, provenance)
    P = pipeline (constraints, limits, fail-closed policy)
    C = context (subject, consent, key, time, purpose)
    S' = transformed state
    R = receipt
    L = ledger entry
"""
from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Spec & Result
# ---------------------------------------------------------------------------

@dataclass
class UMJAMSpec:
    """The contract that a capability must satisfy to be transmuted."""
    operation_id: str
    capability_id: str                 # e.g. "paired_metric_comparison.v1"
    inputs: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    limits: Dict[str, Any] = field(default_factory=dict)   # e.g. {"max_seconds": 60}
    fail_closed: bool = True
    subject: str = ""                  # who/what is affected
    consent: str = "implicit"          # implicit | explicit | n/a
    key: str = ""                      # identity anchor
    purpose: str = ""
    seed: int = 0
    timestamp: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "capability_id": self.capability_id,
            "inputs": self.inputs,
            "constraints": self.constraints,
            "limits": self.limits,
            "fail_closed": self.fail_closed,
            "subject": self.subject,
            "consent": self.consent,
            "key": self.key,
            "purpose": self.purpose,
            "seed": self.seed,
            "timestamp": self.timestamp or int(time.time()),
        }


@dataclass
class UMJAMResult:
    """The output of a UMJAM transmutation: transformed state, receipt, ledger entry."""
    operation_id: str
    capability_id: str
    output: Dict[str, Any] = field(default_factory=dict)
    receipt_hash: str = ""
    ledger_entry: Dict[str, Any] = field(default_factory=dict)
    status: str = "PASS"               # PASS | FAIL | REFUSED
    refusal_reason: str = ""
    timestamp: int = 0
    side_effects: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "capability_id": self.capability_id,
            "output": self.output,
            "receipt_hash": self.receipt_hash,
            "ledger_entry": self.ledger_entry,
            "status": self.status,
            "refusal_reason": self.refusal_reason,
            "timestamp": self.timestamp or int(time.time()),
            "side_effects": self.side_effects,
        }


# ---------------------------------------------------------------------------
# Capability registry (in-memory; persisted by SVCA)
# ---------------------------------------------------------------------------

class CapabilityRegistry:
    """Maps capability_id -> pure-Python callable (Spec, state) -> new state.

    Capabilities are pure: they receive a state and a spec, and return a new
    state dict. They MUST NOT perform side effects on the world.
    """

    def __init__(self) -> None:
        self._caps: Dict[str, Callable[[Dict[str, Any], UMJAMSpec], Dict[str, Any]]] = {}

    def register(self, capability_id: str,
                 fn: Callable[[Dict[str, Any], UMJAMSpec], Dict[str, Any]]) -> None:
        if not capability_id or not isinstance(capability_id, str):
            raise ValueError("capability_id must be a non-empty string")
        self._caps[capability_id] = fn

    def has(self, capability_id: str) -> bool:
        return capability_id in self._caps

    def get(self, capability_id: str):
        return self._caps.get(capability_id)

    def ids(self) -> List[str]:
        return sorted(self._caps.keys())


# ---------------------------------------------------------------------------
# Built-in capabilities
# ---------------------------------------------------------------------------

def _cap_paired_metric_comparison(state: Dict[str, Any],
                                  spec: UMJAMSpec) -> Dict[str, Any]:
    """baseline vs candidate paired metric comparison (bootstrap CI)."""
    import statistics
    baseline = state.get("baseline", [])
    candidate = state.get("candidate", [])
    if not isinstance(baseline, list) or not isinstance(candidate, list):
        return {"error": "baseline and candidate must be lists"}
    n = min(len(baseline), len(candidate))
    if n == 0:
        return {"error": "empty baseline or candidate"}
    diffs = [c - b for b, c in zip(baseline[:n], candidate[:n])]
    mean = sum(diffs) / n
    median = statistics.median(diffs)
    success_rate = sum(1 for d in diffs if d > 0) / n
    # simple bootstrap CI
    rng_seed = spec.seed or 0
    import random
    rng = random.Random(rng_seed)
    boots = []
    for _ in range(min(2000, max(200, n * 10))):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        boots.append(sum(sample) / n)
    boots.sort()
    lo = boots[int(0.025 * len(boots))]
    hi = boots[int(0.975 * len(boots)) - 1]
    return {
        "n": n,
        "mean": round(mean, 4),
        "median": round(median, 4),
        "success_rate": round(success_rate, 4),
        "ci95": [round(lo, 4), round(hi, 4)],
        "improvement": mean > 0,
    }


def _cap_echo(state: Dict[str, Any], spec: UMJAMSpec) -> Dict[str, Any]:
    """Trivial capability: returns the state unchanged. Useful for tests."""
    return {"echo": state}


# ---------------------------------------------------------------------------
# UMJAM
# ---------------------------------------------------------------------------

class UMJAM:
    """Governed transmutation engine.

    Use:
        umjam = UMJAM(registry)
        umjam.registry.register("paired_metric_comparison.v1", _cap_paired_metric_comparison)
        result = umjam.transmute(UMJAMSpec(...), state)
    """

    def __init__(self, registry: Optional[CapabilityRegistry] = None) -> None:
        self.registry = registry or CapabilityRegistry()
        # Auto-register the built-in capabilities
        self.registry.register(
            "paired_metric_comparison.v1", _cap_paired_metric_comparison
        )
        self.registry.register("echo.v1", _cap_echo)

    def transmute(self, spec: UMJAMSpec,
                  state: Dict[str, Any]) -> UMJAMResult:
        # Gate-style checks
        if not isinstance(state, dict):
            return self._refuse(spec, "state must be a dict")
        if not isinstance(spec, UMJAMSpec):
            return self._refuse(spec, "spec must be a UMJAMSpec")
        if not self.registry.has(spec.capability_id):
            return self._refuse(spec, f"unknown capability: {spec.capability_id}")

        cap = self.registry.get(spec.capability_id)
        try:
            new_state = cap(state, spec)
        except Exception as exc:
            return self._refuse(spec, f"capability raised: {exc!r}")

        # Refuse NaN / inf
        if not _state_finite(new_state):
            return self._refuse(spec, "non-finite value in output state")

        ts = int(time.time())
        receipt_hash = self._receipt_hash(spec, new_state, ts)
        ledger_entry = {
            "operation_id": spec.operation_id,
            "capability_id": spec.capability_id,
            "input_hash": hashlib.sha256(
                json.dumps(state, sort_keys=True, default=str).encode()
            ).hexdigest(),
            "output_hash": receipt_hash,
            "status": "PASS",
            "timestamp": ts,
        }
        return UMJAMResult(
            operation_id=spec.operation_id,
            capability_id=spec.capability_id,
            output=new_state,
            receipt_hash=receipt_hash,
            ledger_entry=ledger_entry,
            status="PASS",
            timestamp=ts,
            side_effects=[],
        )

    def _refuse(self, spec: UMJAMSpec, reason: str) -> UMJAMResult:
        return UMJAMResult(
            operation_id=spec.operation_id,
            capability_id=spec.capability_id,
            output={},
            receipt_hash="",
            ledger_entry={"status": "REFUSED", "reason": reason,
                          "timestamp": int(time.time())},
            status="REFUSED",
            refusal_reason=reason,
            timestamp=int(time.time()),
        )

    @staticmethod
    def _receipt_hash(spec: UMJAMSpec, new_state: Dict[str, Any], ts: int) -> str:
        payload = json.dumps(
            {"spec": spec.to_dict(), "output": new_state, "ts": ts},
            sort_keys=True, default=str,
        )
        return hashlib.sha256(payload.encode()).hexdigest()


def _state_finite(state: Any) -> bool:
    """Recursively check that a JSON-like state contains no NaN/inf."""
    if isinstance(state, dict):
        return all(_state_finite(v) for v in state.values())
    if isinstance(state, (list, tuple)):
        return all(_state_finite(v) for v in state)
    if isinstance(state, bool):
        return True
    if isinstance(state, (int, float)):
        import math
        return math.isfinite(float(state))
    return True
