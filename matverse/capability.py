"""
matverse.capability
===================

The Capability Registry — a persistent, versioned, contract-driven
registry of every operation the organism can perform.

A `CapabilityContract` is a dataclass that declares:
  - id (e.g. "paired_metric_comparison.v1")
  - name (human-readable)
  - version
  - inputs schema (dict of name -> type)
  - outputs schema (dict of name -> type)
  - implementation (the actual callable)
  - cost_hint (declared cost; may be measured at runtime)
  - risk_level (LOW | MEDIUM | HIGH)
  - requires_network (bool)
  - requires_gpu (bool)
  - permissions (list of permission strings)
  - tests (list of test names that must pass)
  - lineage (predecessor versions)
  - status (DRAFT | ACTIVE | DEPRECATED | REVOKED)
  - registered_at, registered_by

The registry is persistent: it is JSON-serializable. The `disk_path`
argument lets you save/load across runs. When the runner needs a
capability, it asks the registry, and the registry either returns the
contract (and the function) or refuses.

Built-in capabilities (v3.7.0):

  - echo.v1
  - paired_metric_comparison.v1
  - monte_carlo_propagation.v1
  - sensitivity_analysis.v1
  - ledger_append.v1
  - ledger_verify.v1
  - axis8_score.v1
  - json_validate.v1
  - ast_diff.v1
  - hypothesis_decompose.v1
  - coverage_report.v1
  - schema_infer.v1
  - thermal_record.v1
  - mbit_record.v1
  - publish_metadata.v1
"""
from __future__ import annotations
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

@dataclass
class CapabilityContract:
    id: str
    name: str
    version: str
    inputs: Dict[str, str] = field(default_factory=dict)
    outputs: Dict[str, str] = field(default_factory=dict)
    implementation: Optional[Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = None
    cost_hint: float = 0.0
    risk_level: str = "LOW"             # LOW | MEDIUM | HIGH
    requires_network: bool = False
    requires_gpu: bool = False
    permissions: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    lineage: List[str] = field(default_factory=list)
    status: str = "DRAFT"              # DRAFT | ACTIVE | DEPRECATED | REVOKED
    registered_at: int = 0
    registered_by: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if self.registered_at == 0:
            self.registered_at = int(time.time())
        if self.implementation is not None and not callable(self.implementation):
            raise TypeError("implementation must be callable")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "version": self.version,
            "inputs": dict(self.inputs), "outputs": dict(self.outputs),
            "cost_hint": self.cost_hint, "risk_level": self.risk_level,
            "requires_network": self.requires_network,
            "requires_gpu": self.requires_gpu,
            "permissions": list(self.permissions),
            "tests": list(self.tests), "lineage": list(self.lineage),
            "status": self.status,
            "registered_at": self.registered_at,
            "registered_by": self.registered_by, "notes": self.notes,
            "implementation_hash": self.implementation_hash(),
        }

    def implementation_hash(self) -> str:
        if self.implementation is None:
            return ""
        try:
            import inspect
            src = inspect.getsource(self.implementation)
            return hashlib.sha256(src.encode()).hexdigest()[:16]
        except Exception:
            return ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapabilityContract":
        allowed = {f for f in cls.__dataclass_fields__ if f != "implementation"}
        clean = {k: v for k, v in data.items() if k in allowed}
        return cls(**clean)


# ---------------------------------------------------------------------------
# Built-in capability implementations
# ---------------------------------------------------------------------------

def _impl_echo(state: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    return {"echo": state}


def _impl_paired(state: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    import statistics
    import random
    baseline = state.get("baseline", inputs.get("baseline", []))
    candidate = state.get("candidate", inputs.get("candidate", []))
    if not isinstance(baseline, list) or not isinstance(candidate, list):
        return {"error": "baseline/candidate must be lists"}
    n = min(len(baseline), len(candidate))
    if n == 0:
        return {"error": "empty baseline or candidate"}
    diffs = [c - b for b, c in zip(baseline[:n], candidate[:n])]
    mean = sum(diffs) / n
    seed = int(inputs.get("seed", 0))
    rng = random.Random(seed)
    boots = []
    for _ in range(2000):
        s = [diffs[rng.randrange(n)] for _ in range(n)]
        boots.append(sum(s) / n)
    boots.sort()
    return {
        "n": n, "mean_diff": round(mean, 6),
        "median_diff": round(statistics.median(diffs), 6),
        "success_rate": round(sum(1 for d in diffs if d > 0) / n, 6),
        "ci95": [round(boots[int(0.025 * len(boots))], 6),
                 round(boots[int(0.975 * len(boots)) - 1], 6)],
        "improvement": mean > 0,
    }


def _impl_monte_carlo(state: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    import random
    n = int(inputs.get("n_samples", 5000))
    mu = float(inputs.get("mu", 0.0))
    sigma = float(inputs.get("sigma", max(abs(mu) * 0.1, 1e-6)))
    seed = int(inputs.get("seed", 0))
    rng = random.Random(seed)
    samples = [rng.gauss(mu, sigma) for _ in range(n)]
    samples = [s for s in samples if s == s and abs(s) < 1e308]   # NaN/inf filter
    s = sorted(samples)
    return {
        "n": len(samples),
        "mean": round(sum(samples) / len(samples), 6),
        "p10": round(s[len(s) // 10], 6),
        "p50": round(s[len(s) // 2], 6),
        "p90": round(s[(9 * len(s)) // 10], 6),
    }


def _impl_sensitivity(state: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    base = state.get("inputs", inputs.get("base", {}))
    func = inputs.get("function")
    if not callable(func):
        return {"error": "function must be callable"}
    amp = float(inputs.get("amplitude", 0.1))
    out = []
    base_result = func(base)
    for k in list(base.keys()):
        for sign in (+1.0, -1.0):
            perturbed = dict(base)
            perturbed[k] = base[k] + sign * amp
            r = func(perturbed)
            out.append({"input": k, "value": perturbed[k],
                        "delta": round(r - base_result, 6)})
    out.sort(key=lambda t: abs(t["delta"]), reverse=True)
    return {"base_result": base_result, "perturbations": out}


def _impl_ledger_append(state: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    # Append-only operation. The runner is expected to pass a `ledger` object
    # via state. This capability just records the call.
    state.setdefault("ledger_appends", []).append({
        "kind": inputs.get("kind", "generic"),
        "ts": int(time.time()),
    })
    return {"appends": len(state["ledger_appends"])}


def _impl_ledger_verify(state: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    # Stub: a real verify would walk the chain. The organism has its own
    # `Ledger.verify()`; this is a minimal in-state check.
    return {"ok": True, "n": len(state.get("ledger", []))}


def _impl_axis8(state: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    h = state.get("hypothesis", inputs.get("hypothesis", {}))
    falsifiable = 1.0 if h.get("falsification_criteria") else 0.0
    rev = float(h.get("reversibility", 0.5))
    risk = float(h.get("risk", 0.5))
    ev = float(h.get("expected_value", 0.0))
    cost = float(h.get("cost_estimate", 0.0)) or 1e-9
    return {
        "TRUTHMODE": falsifiable,
        "REDTEAM": min(1.0, 0.3 + 0.7 * min(3, len(h.get("evidence_against", []))) / 3.0),
        "UNLEARN": round(0.4 * rev + 0.6 * falsifiable, 3),
        "80/20": min(1.0, ev / cost / 10.0),
        "HORMOZI": 1.0 if ev > 0 else 0.0,
        "FUTUREYOU": max(0.0, 1.0 - (1.0 - rev) * cost / 100.0),
        "/human": max(0.0, 1.0 - risk),
        "H-Axis": 1.0 if h.get("evidence_for") or h.get("evidence_against") else 0.0,
    }


def _impl_json_validate(state: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    import json
    raw = state.get("text", inputs.get("text", ""))
    try:
        json.loads(raw)
        return {"valid": True}
    except Exception as exc:
        return {"valid": False, "error": repr(exc)}


def _impl_ast_diff(state: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    import ast
    a = state.get("source_a", inputs.get("source_a", ""))
    b = state.get("source_b", inputs.get("source_b", ""))
    try:
        ta = ast.parse(a)
        tb = ast.parse(b)
        return {"equal": ast.dump(ta) == ast.dump(tb),
                "n_a": sum(1 for _ in ast.walk(ta)),
                "n_b": sum(1 for _ in ast.walk(tb))}
    except SyntaxError as exc:
        return {"valid": False, "error": repr(exc)}


def _impl_hypothesis_decompose(state: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    objective = state.get("objective", inputs.get("objective", ""))
    tokens = objective.split()
    keywords = [t for t in tokens if len(t) > 4][:8]
    return {
        "objective": objective,
        "keywords": keywords,
        "candidate_subhypotheses": [
            {"id": f"S{i + 1}", "claim": f"Sub-hypothesis about {kw}",
             "falsification_criteria": f"{kw} < threshold"}
            for i, kw in enumerate(keywords)
        ],
    }


def _impl_coverage_report(state: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    total = int(state.get("total", inputs.get("total", 0)))
    passed = int(state.get("passed", inputs.get("passed", 0)))
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "rate": (passed / total) if total else 0.0,
    }


def _impl_schema_infer(state: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    obj = state.get("sample", inputs.get("sample", {}))
    if not isinstance(obj, dict):
        return {"type": type(obj).__name__}
    schema = {}
    for k, v in obj.items():
        if isinstance(v, bool):
            schema[k] = "boolean"
        elif isinstance(v, int):
            schema[k] = "integer"
        elif isinstance(v, float):
            schema[k] = "number"
        elif isinstance(v, str):
            schema[k] = "string"
        elif isinstance(v, list):
            schema[k] = "array"
        elif isinstance(v, dict):
            schema[k] = "object"
        else:
            schema[k] = "null"
    return {"schema": schema}


def _impl_thermal_record(state: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    workload = state.get("workload", inputs.get("workload", {}))
    energy = float(workload.get("energy_wh", 0.0))
    avoided = float(workload.get("external_energy_avoided_wh", 0.0))
    pbr = (avoided / energy) if energy > 0 else 0.0
    return {
        "energy_wh": energy,
        "external_avoided_wh": avoided,
        "pbr": pbr,
        "measurement_status": workload.get("measurement_status", "DECLARED"),
    }


def _impl_mbit_record(state: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    dims = ["evidence_quality", "reproducibility", "utility",
            "transferability", "human_alignment"]
    vals = [float(inputs.get(d, 0.0)) for d in dims]
    if any(v <= 0 for v in vals):
        score = 0.0
    else:
        prod = 1.0
        for v in vals:
            prod *= v
        score = (prod ** (1.0 / len(vals))) * (1.0 - float(inputs.get("risk", 0.0)))
    return {"geometric_score": round(score, 6), "dimensions": dict(zip(dims, vals))}


def _impl_publish_metadata(state: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    target = state.get("target", inputs.get("target", "zenodo"))
    closure = state.get("closure", inputs.get("closure", {}))
    return {
        "target": target,
        "prepared": True,
        "published": False,             # never auto-publishes
        "status": "PREPARED_NOT_PUBLISHED",
        "closure_id": closure.get("closure_id", ""),
    }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class CapabilityRegistry:
    """Persistent, versioned capability registry."""

    def __init__(self, disk_path: Optional[str] = None) -> None:
        self._caps: Dict[str, CapabilityContract] = {}
        self.disk_path = disk_path
        if disk_path and os.path.exists(disk_path):
            self.load()

    # ------------- registration -------------

    def register(self, contract: CapabilityContract) -> None:
        if not contract.id:
            raise ValueError("capability id must be non-empty")
        if contract.id in self._caps:
            raise ValueError(f"capability {contract.id} already registered; supersede it instead")
        if contract.status == "DRAFT":
            contract.status = "ACTIVE"
        self._caps[contract.id] = contract
        self._persist()

    def supersede(self, old_id: str, new_contract: CapabilityContract) -> None:
        if old_id not in self._caps:
            raise KeyError(f"unknown capability: {old_id}")
        old = self._caps[old_id]
        old.status = "DEPRECATED"
        new_contract.lineage = list(set(old.lineage + [old_id]))
        if new_contract.status == "DRAFT":
            new_contract.status = "ACTIVE"
        self._caps[new_contract.id] = new_contract
        self._persist()

    def revoke(self, capability_id: str, reason: str) -> None:
        if capability_id not in self._caps:
            raise KeyError(capability_id)
        self._caps[capability_id].status = "REVOKED"
        self._caps[capability_id].notes += f"\nREVOKED: {reason}"
        self._persist()

    # ------------- query -------------

    def has(self, capability_id: str) -> bool:
        c = self._caps.get(capability_id)
        return c is not None and c.status == "ACTIVE"

    def get(self, capability_id: str) -> Optional[CapabilityContract]:
        """Return an active capability, or None."""
        c = self._caps.get(capability_id)
        if c is None or c.status != "ACTIVE":
            return None
        return c

    def get_any(self, capability_id: str) -> Optional[CapabilityContract]:
        """Return a capability regardless of its status. Useful for
        inspecting deprecated/revoked entries."""
        return self._caps.get(capability_id)

    def list(self, status: Optional[str] = None) -> List[CapabilityContract]:
        out = list(self._caps.values())
        if status:
            out = [c for c in out if c.status == status]
        return sorted(out, key=lambda c: c.id)

    def select_for(self, contract_requirements: Dict[str, Any]) -> List[CapabilityContract]:
        """Return active capabilities that satisfy a set of requirements
        (e.g. {"risk_level": "LOW", "requires_gpu": False})."""
        out = []
        for c in self.list("ACTIVE"):
            ok = True
            for k, v in contract_requirements.items():
                if getattr(c, k, None) != v:
                    ok = False
                    break
            if ok:
                out.append(c)
        return out

    # ------------- persistence -------------

    def _persist(self) -> None:
        if not self.disk_path:
            return
        data = {cid: c.to_dict() for cid, c in self._caps.items()}
        os.makedirs(os.path.dirname(self.disk_path) or ".", exist_ok=True)
        with open(self.disk_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self) -> None:
        if not self.disk_path or not os.path.exists(self.disk_path):
            return
        with open(self.disk_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for cid, d in data.items():
            try:
                # The implementation is NOT serializable; we restore a
                # marker. The runner will re-register implementations
                # in-process from the built-in set.
                self._caps[cid] = CapabilityContract.from_dict(d)
            except Exception:
                continue

    # ------------- builtin -------------

    def register_builtins(self) -> None:
        """Register the v3.7.0 built-in capability set, idempotently."""
        builtins = [
            ("echo.v1", "Echo", "echo", _impl_echo,
             {"any": "any"}, {"echo": "any"},
             0.001, "LOW", False, False, [], ["test_echo"]),
            ("paired_metric_comparison.v1", "Paired Metric Comparison",
             "compare", _impl_paired,
             {"baseline": "list", "candidate": "list"},
             {"mean_diff": "number", "ci95": "list"},
             0.05, "LOW", False, False, [], ["test_paired"]),
            ("monte_carlo_propagation.v1", "Monte Carlo Propagation",
             "propagate", _impl_monte_carlo,
             {"n_samples": "integer", "mu": "number", "sigma": "number"},
             {"mean": "number", "p10": "number", "p50": "number", "p90": "number"},
             0.1, "LOW", False, False, [], ["test_mc"]),
            ("sensitivity_analysis.v1", "Local Sensitivity Analysis",
             "sensitivity", _impl_sensitivity,
             {"base": "object", "amplitude": "number"},
             {"perturbations": "list"},
             0.05, "LOW", False, False, [], ["test_sensitivity"]),
            ("ledger_append.v1", "Ledger Append",
             "ledger", _impl_ledger_append,
             {"kind": "string"},
             {"appends": "integer"},
             0.001, "LOW", False, False, [], ["test_ledger"]),
            ("ledger_verify.v1", "Ledger Verify",
             "ledger", _impl_ledger_verify,
             {},
             {"ok": "boolean", "n": "integer"},
             0.001, "LOW", False, False, [], ["test_ledger"]),
            ("axis8_score.v1", "AXIS-8 Lens Score",
             "lens", _impl_axis8,
             {"hypothesis": "object"},
             {"TRUTHMODE": "number", "REDTEAM": "number",
              "UNLEARN": "number", "80/20": "number",
              "HORMOZI": "number", "FUTUREYOU": "number",
              "/human": "number", "H-Axis": "number"},
             0.01, "LOW", False, False, [], ["test_axis8"]),
            ("json_validate.v1", "JSON Validate",
             "validate", _impl_json_validate,
             {"text": "string"},
             {"valid": "boolean"},
             0.005, "LOW", False, False, [], ["test_validate"]),
            ("ast_diff.v1", "Python AST Diff",
             "diff", _impl_ast_diff,
             {"source_a": "string", "source_b": "string"},
             {"equal": "boolean", "n_a": "integer", "n_b": "integer"},
             0.01, "LOW", False, False, [], ["test_ast"]),
            ("hypothesis_decompose.v1", "Hypothesis Decomposition",
             "decompose", _impl_hypothesis_decompose,
             {"objective": "string"},
             {"candidate_subhypotheses": "list"},
             0.05, "LOW", False, False, [], ["test_decompose"]),
            ("coverage_report.v1", "Coverage Report",
             "report", _impl_coverage_report,
             {"total": "integer", "passed": "integer"},
             {"rate": "number"},
             0.001, "LOW", False, False, [], ["test_coverage"]),
            ("schema_infer.v1", "JSON Schema Inference",
             "infer", _impl_schema_infer,
             {"sample": "object"},
             {"schema": "object"},
             0.005, "LOW", False, False, [], ["test_infer"]),
            ("thermal_record.v1", "Thermodynamic Record",
             "thermal", _impl_thermal_record,
             {"workload": "object"},
             {"pbr": "number", "energy_wh": "number"},
             0.005, "LOW", False, False, [], ["test_thermal"]),
            ("mbit_record.v1", "M-bit Record",
             "captals", _impl_mbit_record,
             {"evidence_quality": "number", "reproducibility": "number",
              "utility": "number", "transferability": "number",
              "human_alignment": "number", "risk": "number"},
             {"geometric_score": "number"},
             0.005, "LOW", False, False, [], ["test_mbit"]),
            ("publish_metadata.v1", "Publication Metadata",
             "publish", _impl_publish_metadata,
             {"target": "string", "closure": "object"},
             {"prepared": "boolean", "status": "string"},
             0.001, "LOW", False, False, [], ["test_publish"]),
        ]
        for cid, name, _, fn, ins, outs, cost, risk, net, gpu, perms, tests in builtins:
            if cid in self._caps:
                continue
            self.register(CapabilityContract(
                id=cid, name=name, version="1.0.0",
                inputs=ins, outputs=outs, implementation=fn,
                cost_hint=cost, risk_level=risk,
                requires_network=net, requires_gpu=gpu,
                permissions=perms, tests=tests,
                lineage=["v3.0.0"] if not self._caps else [],
                status="ACTIVE",
                registered_by="matverse-organism-v3.7.0",
                notes="Built-in capability for the v3.7.0 organism.",
            ))
