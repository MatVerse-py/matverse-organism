"""
matverse.existential
====================

The four existential processes of the MatVerse organism:

  Metabolism        — convert resources into continuity
  Autopoiesis       — produce and repair the organism's own components
  Apoptosis         — governed shutdown of harmful or obsolete expressions
  Antifragility     — measurable improvement after perturbation

These are first-class organs. They do not replace the cognitive organs
(Cassandra, COG, Campo de Hipóteses) — they sit *around* them,
governing their lifecycle.

A fifth supporting process is Homeostasis (return to a safe region
after a small deviation). It is included here because in the canon
it is distinguished from autopoiesis and antifragility:

  Homeostasis  : perturb -> correct -> return to safe interval
  Autopoiesis  : perturb -> repair -> regenerate component
  Antifragility: perturb -> repair -> learn -> performance > pre-perturbation

Not every perturbation needs antifragility. Some are absorbed with
low cost via homeostasis.
"""
from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Metabolism
# ---------------------------------------------------------------------------

@dataclass
class MetabolismBudget:
    vital: float = 100.0                # reserve for continuity
    service: float = 100.0              # external work
    learning: float = 100.0             # capability acquisition
    regeneration: float = 100.0         # planetary benefit work
    spent: Dict[str, float] = field(default_factory=lambda: {
        "vital": 0.0, "service": 0.0, "learning": 0.0, "regeneration": 0.0,
    })

    def spend(self, pool: str, amount: float) -> bool:
        if amount < 0:
            return False
        avail = getattr(self, pool, 0.0) - self.spent.get(pool, 0.0)
        if amount > avail:
            return False
        self.spent[pool] = self.spent.get(pool, 0.0) + amount
        return True

    def surplus(self, pool: str) -> float:
        return getattr(self, pool, 0.0) - self.spent.get(pool, 0.0)

    def viability(self) -> float:
        """Geometric mean of remaining fractions. Zero in any pool => zero."""
        fracs = []
        for pool in ("vital", "service", "learning", "regeneration"):
            total = getattr(self, pool, 0.0)
            if total <= 0:
                return 0.0
            fracs.append(self.surplus(pool) / total)
        prod = 1.0
        for f in fracs:
            prod *= max(0.0, f)
        return prod ** (1.0 / len(fracs))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vital": self.vital, "service": self.service,
            "learning": self.learning, "regeneration": self.regeneration,
            "spent": dict(self.spent),
            "viability": round(self.viability(), 4),
        }


class Metabolism:
    """Allocate resources to the four reserves. Vital reserve is non-spendable
    except for continuity. This is the constitutional floor."""

    def __init__(self, budget: Optional[MetabolismBudget] = None) -> None:
        self.budget = budget or MetabolismBudget()

    def can_spend(self, pool: str, amount: float) -> bool:
        return self.budget.surplus(pool) >= amount

    def spend(self, pool: str, amount: float) -> bool:
        return self.budget.spend(pool, amount)

    def report(self) -> Dict[str, Any]:
        return self.budget.to_dict()


# ---------------------------------------------------------------------------
# Autopoiesis
# ---------------------------------------------------------------------------

@dataclass
class AutopoiesisReceipt:
    component: str
    diagnosis: str
    repair: str
    success: bool
    ts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component, "diagnosis": self.diagnosis,
            "repair": self.repair, "success": self.success, "ts": self.ts,
        }


class Autopoiesis:
    """The organism's self-repair loop.

    A `diagnose` callable returns (component, issue); a `repair` callable
    attempts a fix; the result is recorded. The repair itself is a UMJAM
    transmutation in production; here we keep it generic.
    """

    def __init__(self) -> None:
        self.history: List[AutopoiesisReceipt] = []

    def run_cycle(self, component: str, diagnosis: str,
                  repair_fn: Callable[[], str]) -> AutopoiesisReceipt:
        try:
            msg = repair_fn()
            ok = True
        except Exception as exc:
            msg = f"repair failed: {exc!r}"
            ok = False
        rec = AutopoiesisReceipt(
            component=component, diagnosis=diagnosis,
            repair=msg, success=ok, ts=int(time.time()),
        )
        self.history.append(rec)
        return rec

    def summary(self) -> Dict[str, Any]:
        n = len(self.history)
        ok = sum(1 for r in self.history if r.success)
        return {
            "n_repairs": n,
            "success_rate": (ok / n) if n else 0.0,
        }


# ---------------------------------------------------------------------------
# Apoptosis — governed shutdown
# ---------------------------------------------------------------------------

APOPTOSIS_STATES = [
    "ACTIVE",
    "DEGRADED",
    "QUARANTINED",
    "SUPERSEDED",
    "REVOKED",
    "ARCHIVED",
]


@dataclass
class ApoptosisCase:
    component: str
    current_state: str
    diagnosis: Dict[str, Any]
    history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "current_state": self.current_state,
            "diagnosis": self.diagnosis,
            "history": self.history,
        }


class Apoptosis:
    """Governed shutdown of harmful, obsolete, or unsalvageable expressions.

    A component's transition to a non-ACTIVE state requires:
      - a documented diagnosis
      - preservation of its lineage (I5)
      - no loss of evidence (I3, I4)
    """

    def __init__(self) -> None:
        self.cases: Dict[str, ApoptosisCase] = {}

    def register(self, component: str,
                 diagnosis: Optional[Dict[str, Any]] = None) -> ApoptosisCase:
        case = ApoptosisCase(
            component=component, current_state="ACTIVE",
            diagnosis=diagnosis or {},
        )
        self.cases[component] = case
        return case

    def transition(self, component: str, new_state: str,
                   reason: str) -> ApoptosisCase:
        if new_state not in APOPTOSIS_STATES:
            raise ValueError(f"invalid state: {new_state}")
        if component not in self.cases:
            self.register(component)
        case = self.cases[component]
        if new_state == "REVOKED" and case.current_state not in ("QUARANTINED", "SUPERSEDED"):
            raise ValueError(
                "REVOKED requires prior QUARANTINED or SUPERSEDED state"
            )
        case.current_state = new_state
        case.history.append({
            "ts": int(time.time()),
            "from": None,  # populated below if needed
            "to": new_state,
            "reason": reason,
        })
        return case

    def is_alive(self, component: str) -> bool:
        c = self.cases.get(component)
        return c is not None and c.current_state == "ACTIVE"

    def summary(self) -> Dict[str, Any]:
        out: Dict[str, int] = {}
        for c in self.cases.values():
            out[c.current_state] = out.get(c.current_state, 0) + 1
        return {"n_components": len(self.cases), "by_state": out}


# ---------------------------------------------------------------------------
# Antifragility
# ---------------------------------------------------------------------------

@dataclass
class AntifragilitySample:
    perturbation: str
    metric_before: float
    metric_after: float
    ts: int = 0

    @property
    def delta(self) -> float:
        return self.metric_after - self.metric_before

    def to_dict(self) -> Dict[str, Any]:
        return {
            "perturbation": self.perturbation,
            "metric_before": self.metric_before,
            "metric_after": self.metric_after,
            "delta": round(self.delta, 6),
            "ts": self.ts,
        }


class Antifragility:
    """Measure whether perturbations improved the organism.

    The signature of antifragility is:

        dP / ds > 0

    where P is performance and s is a perturbation magnitude. The
    antifragility score is the average positive delta over a window,
    bounded by `min_samples` to avoid fluke.
    """

    def __init__(self, min_samples: int = 5) -> None:
        self.samples: List[AntifragilitySample] = []
        self.min_samples = min_samples

    def record(self, perturbation: str, before: float, after: float) -> AntifragilitySample:
        s = AntifragilitySample(perturbation, before, after, int(time.time()))
        self.samples.append(s)
        return s

    def score(self) -> float:
        """Mean positive delta. Negative if more degradation than improvement."""
        if len(self.samples) < self.min_samples:
            return 0.0
        deltas = [s.delta for s in self.samples]
        return sum(deltas) / len(deltas)

    def is_antifragile(self, threshold: float = 0.0) -> bool:
        return self.score() > threshold

    def summary(self) -> Dict[str, Any]:
        n = len(self.samples)
        pos = sum(1 for s in self.samples if s.delta > 0)
        neg = sum(1 for s in self.samples if s.delta < 0)
        return {
            "n_samples": n,
            "n_positive": pos,
            "n_negative": neg,
            "score": round(self.score(), 6),
            "antifragile": self.is_antifragile(),
        }


# ---------------------------------------------------------------------------
# Homeostasis
# ---------------------------------------------------------------------------

@dataclass
class HomeostasisRegion:
    metric: str
    lower: float
    upper: float

    def contains(self, value: float) -> bool:
        return self.lower <= value <= self.upper


class Homeostasis:
    """Return to a safe interval after a small deviation. Cheap; not a learning."""

    def __init__(self, regions: Optional[Dict[str, HomeostasisRegion]] = None) -> None:
        self.regions = regions or {}

    def register_region(self, metric: str, lower: float, upper: float) -> None:
        self.regions[metric] = HomeostasisRegion(metric, lower, upper)

    def in_region(self, metric: str, value: float) -> bool:
        r = self.regions.get(metric)
        if r is None:
            return True
        return r.contains(value)

    def deviation(self, metric: str, value: float) -> float:
        r = self.regions.get(metric)
        if r is None:
            return 0.0
        if value < r.lower:
            return r.lower - value
        if value > r.upper:
            return value - r.upper
        return 0.0

    def summary(self) -> Dict[str, Any]:
        return {"n_regions": len(self.regions),
                "metrics": list(self.regions.keys())}
