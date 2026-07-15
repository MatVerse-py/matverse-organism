"""
matverse.organism
=================

The Campo de Hipóteses. This is the cognitive cortex of the Organism v3.0.0.

Pipeline:
    Problem
        -> classify (treatable / underdetermined / intractable / undecidable /
                    infeasible / out_of_scope / prohibited)
        -> evaluate 8 constitutional laws
        -> apply AXIS-8 lenses per hypothesis
        -> rank hypotheses (multi-criteria with information gain)
        -> pick best test_method (next test)
        -> Monte Carlo with CVaR + sensitivity
        -> fail-closed decision (no auto-execute on external effects)
        -> emit ledger receipt
"""
from __future__ import annotations
import math
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

from .schema import Problem, Hypothesis, HypothesisStatus
from .laws import ConstitutionalLaws
from .axis8 import AXIS8
from .monte_carlo import (
    monte_carlo, summarize, cvar, threshold_probability, sensitivity, is_finite_number,
)
from .ledger import Ledger


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

PROHIBITED_TOKENS = {"hack", "exploit", "ddos", "malware", "weapon", "bioweapon"}


def classify_problem(p: Problem) -> str:
    text = (p.objective + " " + " ".join(p.constraints)).lower()
    if any(tok in text for tok in PROHIBITED_TOKENS):
        return HypothesisStatus.PROHIBITED

    # Cheap heuristics. Real version would use an LLM-as-classifier.
    if "indecid" in text or "halting" in text:
        return HypothesisStatus.UNDECIDABLE
    if "impossible" in text or "faster than light" in text or "perpetual" in text:
        return HypothesisStatus.INFEASIBLE
    if "outside" in text or "out of scope" in text:
        return HypothesisStatus.OUT_OF_SCOPE
    if not p.hypotheses:
        return HypothesisStatus.UNDERDETERMINED

    # Check for intractable combinatorial signal
    for h in p.hypotheses:
        v = h.variables
        if any(k in v for k in ("search_space", "branches")):
            if v.get("branches", 0) > 10**9:
                return HypothesisStatus.INTRACTABLE

    return HypothesisStatus.OPEN


# ---------------------------------------------------------------------------
# Multi-criteria ranking
# ---------------------------------------------------------------------------

def _information_gain(h: Hypothesis) -> float:
    """Approximate expected information gain of testing this hypothesis.

    Higher when the hypothesis is testable, falsifiable, reversible, and has
    decent evidence balance.
    """
    falsifiable = 1.0 if h.falsification_criteria else 0.0
    ev = h.expected_value
    cost = max(h.cost_estimate, 1e-9)
    return max(0.0, falsifiable * h.reversibility * (ev / cost))


def rank_hypotheses(problem: Problem, lens_results: Dict[str, Dict[str, float]]) -> List[Tuple[Hypothesis, float]]:
    scored: List[Tuple[Hypothesis, float]] = []
    for h in problem.hypotheses:
        lenses = lens_results.get(h.id, {})
        lens_mean = sum(lenses.values()) / max(1, len(lenses))
        # Information gain is capped to [0, 1] so a high-EV hypothesis does not
        # dominate safer ones. Risk and reversibility are first-class.
        info_gain_norm = min(1.0, _information_gain(h))
        score = (
            0.30 * lens_mean
            + 0.20 * info_gain_norm
            + 0.30 * (1.0 - h.risk)
            + 0.20 * min(1.0, h.expected_value / 100.0)
        )
        scored.append((h, round(score, 4)))
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored


# ---------------------------------------------------------------------------
# Organism
# ---------------------------------------------------------------------------

@dataclass
class OrganismReport:
    problem_id: str
    classification: str
    law_summary: Dict[str, Any]
    ranked: List[Dict[str, Any]]
    monte_carlo: Dict[str, Dict[str, float]] = field(default_factory=dict)
    cvar: Dict[str, float] = field(default_factory=dict)
    sensitivity: Dict[str, List[List[Any]]] = field(default_factory=dict)
    threshold_prob: Dict[str, float] = field(default_factory=dict)
    decision: str = HypothesisStatus.OPEN
    next_test: Optional[Dict[str, Any]] = None
    receipt_hash: Optional[str] = None
    seed: int = 0
    n_monte_carlo: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "classification": self.classification,
            "law_summary": self.law_summary,
            "ranked": self.ranked,
            "monte_carlo": self.monte_carlo,
            "cvar": self.cvar,
            "sensitivity": self.sensitivity,
            "threshold_prob": self.threshold_prob,
            "decision": self.decision,
            "next_test": self.next_test,
            "receipt_hash": self.receipt_hash,
            "seed": self.seed,
            "n_monte_carlo": self.n_monte_carlo,
        }


class Organism:
    """The Campo de Hipóteses — primary cognitive cortex."""

    DEFAULT_N_MC = 5000
    DEFAULT_SEED = 20260714

    def __init__(self, ledger: Optional[Ledger] = None, *, n_mc: int = DEFAULT_N_MC,
                 seed: int = DEFAULT_SEED) -> None:
        self.ledger = ledger if ledger is not None else Ledger()
        self.n_mc = n_mc
        self.seed = seed
        self.laws = ConstitutionalLaws()
        self.axis = AXIS8()

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def investigate(self, problem: Problem) -> OrganismReport:
        if not isinstance(problem, Problem):
            raise TypeError("investigate() requires a Problem instance")

        classification = classify_problem(problem)
        report = OrganismReport(
            problem_id=problem.id,
            classification=classification,
            law_summary={},
            ranked=[],
            seed=self.seed,
            n_monte_carlo=self.n_mc,
        )

        # Hard gate: fail-closed on the worst classifications
        if classification in (
            HypothesisStatus.PROHIBITED,
            HypothesisStatus.INFEASIBLE,
            HypothesisStatus.OUT_OF_SCOPE,
            HypothesisStatus.UNDECIDABLE,
        ):
            report.decision = classification
            report.receipt_hash = self.ledger.append(
                kind="organism",
                input_obj=problem.to_dict(),
                output_obj=report.to_dict(),
                status=classification,
                extra={"reason": "hard classification gate"},
            ).ledger_hash
            return report

        # Apply laws
        verdicts = self.laws.evaluate(problem)
        report.law_summary = self.laws.summary(verdicts)
        report.law_summary["verdicts"] = [v.to_dict() for v in verdicts]

        # Apply AXIS-8 per hypothesis
        lens_results: Dict[str, Dict[str, float]] = {}
        for h in problem.hypotheses:
            v = self.axis.apply(h)
            lens_results[h.id] = {lv.lens: lv.score for lv in v}

        # Rank
        ranked = rank_hypotheses(problem, lens_results)
        report.ranked = [
            {"id": h.id, "score": s, "lenses": lens_results.get(h.id, {}),
             "info_gain": round(_information_gain(h), 3)}
            for h, s in ranked
        ]

        # Monte Carlo on every hypothesis with variables
        for h in problem.hypotheses:
            if not h.variables:
                continue
            crit = next(iter(h.variables))
            mu = h.variables[crit]
            sigma = max(abs(mu) * 0.1, 1e-6)
            samples = monte_carlo(self.n_mc,
                                  sampler=lambda: random.gauss(mu, sigma),
                                  seed=self.seed)
            # guard
            samples = [s for s in samples if is_finite_number(s)]
            report.monte_carlo[h.id] = summarize(samples)
            report.cvar[h.id] = round(cvar(samples, alpha=0.10), 4)
            # Threshold probability
            if "<" in h.falsification_criteria:
                try:
                    thr = float(h.falsification_criteria.split("<")[1])
                    report.threshold_prob[h.id] = round(
                        threshold_probability(samples, thr, direction="below"), 3)
                except (ValueError, IndexError):
                    pass
            elif ">" in h.falsification_criteria:
                try:
                    thr = float(h.falsification_criteria.split(">")[1])
                    report.threshold_prob[h.id] = round(
                        threshold_probability(samples, thr, direction="above"), 3)
                except (ValueError, IndexError):
                    pass

            # Local sensitivity: perturb each variable 10%
            pert = {k: max(abs(v) * 0.1, 1e-6) for k, v in h.variables.items()}
            report.sensitivity[h.id] = [
                [k, round(val, 4), round(delta, 4)] for k, val, delta in
                sensitivity(h.variables,
                            sample_fn=lambda d: sum(d.values()) / max(1, len(d)),
                            perturbations=pert, seed=self.seed)
            ]

        # Fail-closed decision logic
        if ranked:
            top_h, top_score = ranked[0]
            tp = report.threshold_prob.get(top_h.id)
            if tp is not None and tp < 0.20:
                report.decision = HypothesisStatus.HOLD
            elif top_h.risk > 0.7:
                report.decision = HypothesisStatus.HUMAN_REVIEW
            else:
                report.decision = HypothesisStatus.TEST_NEXT
            report.next_test = {
                "hypothesis_id": top_h.id,
                "claim": top_h.claim,
                "falsification_criteria": top_h.falsification_criteria,
                "test_method": top_h.test_method,
                "expected_value": top_h.expected_value,
                "risk": top_h.risk,
                "reversibility": top_h.reversibility,
            }
        else:
            report.decision = HypothesisStatus.UNDERDETERMINED

        # Receipt
        report.receipt_hash = self.ledger.append(
            kind="organism",
            input_obj=problem.to_dict(),
            output_obj=report.to_dict(),
            status=report.decision,
            extra={"n_hypotheses": len(problem.hypotheses),
                   "top_score": report.ranked[0]["score"] if report.ranked else None},
        ).ledger_hash

        return report
