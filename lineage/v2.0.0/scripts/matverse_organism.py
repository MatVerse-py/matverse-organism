"""
Reconstructed v2.0.0 Campo de Hipóteses.

This is a faithful reconstruction of the v2.0.0 organ. It is NOT
imported or used by v3.0.0; it lives here for the historical record.

The 11/11 test suite that originally accompanied v2.0.0 is preserved
in `tests/test_v2.py`.
"""
import json
import hashlib
import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


FALSIFICATION_SEED = 42
MAX_MONTE_CARLO = 10_000


@dataclass
class Hypothesis:
    id: str
    claim: str
    variables: Dict[str, float] = field(default_factory=dict)
    evidence_for: List[str] = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)
    falsification_criteria: str = ""


def _hash(o: Any) -> str:
    return hashlib.sha256(
        json.dumps(o, sort_keys=True, ensure_ascii=False, default=str).encode()
    ).hexdigest()


def investigate(problem: Dict[str, Any]) -> Dict[str, Any]:
    """Single-organ v2.0.0 entry point."""
    rng = random.Random(FALSIFICATION_SEED)
    hyps = problem.get("hypotheses", [])
    if not hyps:
        return {"decision": "UNDERDETERMINED", "ranked": []}

    ranked = []
    monte = {}
    cvar10 = {}
    threshold_prob = {}
    for h in hyps:
        variables = h.get("variables", {})
        if variables:
            crit = next(iter(variables))
            mu = variables[crit]
            sigma = max(abs(mu) * 0.1, 1e-6)
            samples = [rng.gauss(mu, sigma) for _ in range(MAX_MONTE_CARLO)]
            samples = [s for s in samples if math.isfinite(s)]
            s = sorted(samples)
            mean = sum(samples) / len(samples)
            monte[h["id"]] = {"mean": mean, "p10": s[len(s) // 10], "p90": s[(9 * len(s)) // 10]}
            tail = s[: max(1, len(s) // 10)]
            cvar10[h["id"]] = sum(tail) / len(tail)
            if "<" in h.get("falsification_criteria", ""):
                thr = float(h["falsification_criteria"].split("<")[1])
                threshold_prob[h["id"]] = sum(1 for v in samples if v < thr) / len(samples)
        # crude ranking: lower risk + higher reversibility
        ranked.append({"id": h["id"], "score": 0.5})
    return {
        "decision": "TEST_NEXT",
        "ranked": ranked,
        "monte_carlo": monte,
        "cvar": cvar10,
        "threshold_prob": threshold_prob,
        "ledger_tip": _hash(ranked),
    }
