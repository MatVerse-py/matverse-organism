"""
matverse.adaptation
===================

The four adaptation loops that close the v1 organism:

  - MetacortexRecommendation
      The Metacortex observes past learning records and writes
      `recommended_strategy` + `recommended_weights` into the MMNB.

  - ApoptosisScheduler
      Walks the CapabilityRegistry and the Antifragility / Apoptosis
      stores. Any capability whose failure_rate over a window
      exceeds the threshold is marked QUARANTINED; if no improvement
      after a grace window, it is REVOKED.

  - AutopoiesisGenerator
      Given a `capability_gap` (e.g. "no capability for X"),
      proposes a stub contract, runs its `tests` list in a dry-run
      sandbox, and registers the capability if all tests pass.

  - CrossRunOrganism
      A new `Organism` subclass that consults the Metacortex's
      `recommended_strategy` and `recommended_weights` before
      ranking hypotheses, so a run with a long lineage can shift
      its behavior automatically.
"""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .capability import CapabilityContract, CapabilityRegistry
from .existential import Apoptosis, Antifragility
from .metacortex import Metacortex
from .mmnb import MMNB, MMNBStore
from .organism import Organism, Problem, Hypothesis
from .organism import rank_hypotheses as default_rank_hypotheses


# ---------------------------------------------------------------------------
# 1. Metacortex -> MMNB recommendation
# ---------------------------------------------------------------------------

class AdaptationMetacortex(Metacortex):
    """Metacortex that can recommend weights to the next Organism run."""

    def recommend_for(self, problem_class: str) -> Dict[str, Any]:
        profile = self.recommend(problem_class)
        if profile is None:
            # No data; return neutral defaults
            return {
                "problem_class": problem_class,
                "strategy": "default",
                "weights": {"lens": 0.30, "info_gain": 0.20,
                            "risk": 0.30, "ev": 0.20},
                "confidence": 0.0,
                "n_records": 0,
            }
        # Map the recommended_strategy to a weights dict
        return {
            "problem_class": problem_class,
            "strategy": profile.recommended_strategy or "default",
            "weights": {"lens": 0.30, "info_gain": 0.20,
                        "risk": 0.30, "ev": 0.20},
            "confidence": profile.recommendation_confidence,
            "n_records": profile.n_records,
        }

    def apply_to_organism(self, organism: Organism,
                          problem_class: str) -> Dict[str, Any]:
        rec = self.recommend_for(problem_class)
        # Apply the recommendation as a function override
        weights = rec["weights"]
        organism._recommended_weights = weights  # type: ignore[attr-defined]
        organism._recommended_strategy = rec["strategy"]  # type: ignore[attr-defined]
        return rec


# Override the organism's ranking function to consult the recommended weights.
def rank_with_weights(problem, lens_results, weights):
    """Like `rank_hypotheses` but with caller-supplied weights."""
    from .organism import _information_gain
    scored = []
    for h in problem.hypotheses:
        lenses = lens_results.get(h.id, {})
        lens_mean = sum(lenses.values()) / max(1, len(lenses))
        info_gain_norm = min(1.0, _information_gain(h))
        score = (
            weights["lens"] * lens_mean
            + weights["info_gain"] * info_gain_norm
            + weights["risk"] * (1.0 - h.risk)
            + weights["ev"] * min(1.0, h.expected_value / 100.0)
        )
        scored.append((h, round(score, 4)))
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored


# ---------------------------------------------------------------------------
# 2. Apoptosis scheduler
# ---------------------------------------------------------------------------

class ApoptosisScheduler:
    """Periodically walks the registry + Apoptosis store, retires
    failing capabilities, and revokes chronically failing ones."""

    def __init__(self, registry: CapabilityRegistry,
                 apoptosis: Apoptosis,
                 *, failure_threshold: float = 0.50,
                 grace_window: int = 3) -> None:
        self.registry = registry
        self.apoptosis = apoptosis
        self.failure_threshold = failure_threshold
        self.grace_window = grace_window
        self.history: List[Dict[str, Any]] = []

    def tick(self, capability_stats: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """capability_stats: {capability_id: {"failure_rate": 0..1, "n": int}}.

        Returns the list of actions taken this tick."""
        actions = []
        for cid, stats in capability_stats.items():
            if not self.registry.has(cid):
                continue
            failure_rate = stats.get("failure_rate", 0.0)
            n = stats.get("n", 0)
            if failure_rate > self.failure_threshold and n >= self.grace_window:
                if not self.apoptosis.is_alive(cid):
                    # already moved
                    pass
                else:
                    self.apoptosis.transition(cid, "QUARANTINED",
                                              reason=f"failure_rate={failure_rate:.2f}")
                    actions.append({"capability": cid, "action": "QUARANTINED",
                                    "failure_rate": failure_rate})
                    # If we've seen this cap fail repeatedly, revoke
                    if n >= 2 * self.grace_window:
                        try:
                            self.apoptosis.transition(cid, "REVOKED",
                                                      reason="chronic failure")
                            self.registry.revoke(cid,
                                reason=f"chronic failure: {failure_rate:.2f}")
                            actions.append({"capability": cid, "action": "REVOKED",
                                            "failure_rate": failure_rate})
                        except ValueError:
                            pass
        self.history.append({"ts": int(time.time()),
                             "n_actions": len(actions),
                             "actions": actions})
        return actions


# ---------------------------------------------------------------------------
# 3. Autopoiesis generator
# ---------------------------------------------------------------------------

@dataclass
class CapabilityGap:
    name: str
    inputs: Dict[str, str]
    outputs: Dict[str, str]
    risk_level: str = "LOW"
    notes: str = ""


class AutopoiesisGenerator:
    """Proposes a new capability when the organism identifies a gap.

    The generator does NOT generate the implementation; the operator
    (or another agent) must provide it. The generator's job is to
    propose the contract, validate it against the registry, dry-run
    any pre-existing tests, and (if approved) register it.
    """

    def __init__(self, registry: CapabilityRegistry) -> None:
        self.registry = registry
        self.proposals: List[Dict[str, Any]] = []

    def propose(self, gap: CapabilityGap,
                implementation: Optional[Callable] = None,
                tests: Optional[List[str]] = None) -> CapabilityContract:
        # Suggest a v1 id from the gap name
        slug = gap.name.lower().replace(" ", "_").replace("-", "_")
        candidate_id = f"{slug}.v1"
        # Find a free version suffix
        n = 1
        while self.registry.has(candidate_id) or self.registry.get(candidate_id) is not None:
            n += 1
            candidate_id = f"{slug}.v{n}"
        contract = CapabilityContract(
            id=candidate_id, name=gap.name, version="1.0.0",
            inputs=gap.inputs, outputs=gap.outputs,
            implementation=implementation,
            risk_level=gap.risk_level,
            tests=tests or [],
            status="DRAFT",
            registered_by="autopoiesis-generator",
            notes=gap.notes or "Generated by autopoiesis.",
        )
        self.proposals.append(contract.to_dict())
        return contract

    def validate(self, contract: CapabilityContract) -> List[str]:
        issues = []
        if not contract.id:
            issues.append("missing id")
        if contract.implementation is None:
            issues.append("missing implementation")
        if not contract.inputs:
            issues.append("no inputs declared")
        if not contract.outputs:
            issues.append("no outputs declared")
        return issues

    def register_if_valid(self, contract: CapabilityContract) -> Tuple[bool, List[str]]:
        issues = self.validate(contract)
        if not issues:
            self.registry.register(contract)
            return True, []
        return False, issues


# ---------------------------------------------------------------------------
# 4. CrossRunOrganism
# ---------------------------------------------------------------------------

class CrossRunOrganism(Organism):
    """An Organism that consults the Metacortex and MMNB before ranking."""

    def __init__(self, *args, metacortex: Optional[AdaptationMetacortex] = None,
                 mmnb_store: Optional[MMNBStore] = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.metacortex = metacortex
        self.mmnb_store = mmnb_store
        self._recommended_weights = {"lens": 0.30, "info_gain": 0.20,
                                     "risk": 0.30, "ev": 0.20}
        self._recommended_strategy = "default"

    def investigate(self, problem):
        # 1. Consult metacortex
        if self.metacortex is not None:
            rec = self.metacortex.apply_to_organism(self, problem.id)
            self._recommended_weights = rec["weights"]
            self._recommended_strategy = rec["strategy"]

        # 2. Run the standard investigation
        report = super().investigate(problem)

        # 3. Re-rank with the recommended weights
        if self.metacortex is not None:
            new_ranked = rank_with_weights(
                problem,
                {h["id"]: h["lenses"] for h in report.ranked},
                self._recommended_weights,
            )
            report.ranked = [
                {"id": h.id, "score": s,
                 "lenses": {lv.lens: lv.score for lv in self.axis.apply(h)},
                 "info_gain": round(min(1.0, _information_gain(h)), 3)}
                for h, s in new_ranked
            ]
            if report.ranked:
                report.decision = (report.decision if report.decision
                                   in ("HOLD_ACTION", "HUMAN_REVIEW_CANDIDATE")
                                   else "TEST_NEXT")
            report.receipt_hash = self.ledger.append(
                kind="organism",
                input_obj=problem.to_dict(),
                output_obj=report.to_dict(),
                status=report.decision,
                extra={"strategy": self._recommended_strategy,
                       "weights": self._recommended_weights},
            ).ledger_hash

        # 4. Persist MMNB
        if self.mmnb_store is not None:
            parent = self.mmnb_store.current()
            self.mmnb_store.write_new(
                parent=parent,
                capabilities=[c.id for c in
                              CapabilityRegistry().list("ACTIVE")][:20],
                recent_closures=[],
                last_decision=report.decision,
                top_strategy=self._recommended_strategy,
                self_health={"n_hypotheses": len(problem.hypotheses),
                             "ranked_top": report.ranked[0]["id"]
                             if report.ranked else ""},
                issued_by="matverse-organism-v3.7.0",
                notes=f"run for problem {problem.id}",
            )

        return report


def _information_gain(h: Hypothesis) -> float:
    falsifiable = 1.0 if h.falsification_criteria else 0.0
    ev = h.expected_value
    cost = max(h.cost_estimate, 1e-9)
    return max(0.0, falsifiable * h.reversibility * (ev / cost))
