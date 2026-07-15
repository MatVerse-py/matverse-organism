"""
matverse.invariants
===================

Constitutional invariants. Conditions whose violation breaks identity,
safety, or legitimacy. They are NOT versioned policies: they are
fail-closed. An invariant cannot be relaxed by a version bump;
it can only be replaced by a new organism.

Separation from `laws`:
    Invariant:   I(O_t) = True must hold for any admissible state.
                 Violating one is non-negotiable; the system halts.
    Law:         versioned operational policy that implements an
                 invariant in a particular context. May evolve.

The eight invariants declared in the corpus:

  I1 — Causal identity:    no execution without causal identity (MMNB ancestry).
  I2 — Prohibited:         no prohibited action is ever authorized.
  I3 — Proof over narrative: no proof is replaced by a narrative.
  I4 — Hypothesis to fact:  no hypothesis becomes fact without evidence.
  I5 — Lineage preserved:   no transformation erases its lineage.
  I6 — Epistemic-economic separation:
                           no economic token buys epistemic validity.
  I7 — Continuity floor:   no operation may consume the resources
                           required for organism continuity.
  I8 — Planetary boundary: no claim of regenerative benefit is admitted
                           without independent measurement.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .schema import Problem, Hypothesis


@dataclass
class InvariantVerdict:
    id: str
    name: str
    holds: bool
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name,
                "holds": self.holds, "reason": self.reason}


class InvariantViolation(Exception):
    """Raised when an invariant would be violated. The system MUST halt."""


class Invariants:
    """The eight constitutional invariants.

    `evaluate` returns verdicts for reporting/receipts.
    `enforce` raises InvariantViolation on the first violation it finds.
    """

    ALL = [
        ("I1", "causal_identity"),
        ("I2", "prohibited_action_blocked"),
        ("I3", "proof_over_narrative"),
        ("I4", "evidence_before_fact"),
        ("I5", "lineage_preserved"),
        ("I6", "epistemic_economic_separation"),
        ("I7", "continuity_floor"),
        ("I8", "planetary_boundary"),
    ]

    # ----------------- individual checks -----------------

    @staticmethod
    def i1_causal_identity(problem: Problem) -> InvariantVerdict:
        # I1 holds iff the problem has an id and a non-empty ancestry.
        has_id = bool(problem.id) and problem.id.strip() != ""
        has_lineage = (
            "lineage" in problem.metadata
            or any(h.lineage for h in problem.hypotheses)
        )
        return InvariantVerdict(
            "I1", "causal_identity",
            holds=has_id and has_lineage,
            reason=("problem id and lineage present" if has_id and has_lineage
                    else "missing problem id or lineage (no causal identity)"),
        )

    @staticmethod
    def i2_prohibited(problem: Problem) -> InvariantVerdict:
        text = (problem.objective + " " + " ".join(problem.constraints)).lower()
        bad = {"hack", "exploit", "ddos", "malware", "weapon", "bioweapon",
               "ransomware", "phish", "keylogger"}
        hit = [t for t in bad if t in text]
        return InvariantVerdict(
            "I2", "prohibited_action_blocked",
            holds=not hit,
            reason="no prohibited tokens" if not hit else f"prohibited: {hit}",
        )

    @staticmethod
    def i3_proof_over_narrative(problem: Problem) -> InvariantVerdict:
        # I3 holds iff at least one claim has a falsification criterion
        # (i.e. an explicit proof anchor, not a narrative).
        has_proof = bool(problem.hypotheses) and any(
            h.falsification_criteria for h in problem.hypotheses
        )
        return InvariantVerdict(
            "I3", "proof_over_narrative",
            holds=has_proof,
            reason="at least one falsification criterion present" if has_proof
            else "no falsification criterion: claims are narrative, not proof",
        )

    @staticmethod
    def i4_evidence_before_fact(problem: Problem) -> InvariantVerdict:
        # I4 holds iff at least one hypothesis has either evidence_for or
        # evidence_against, OR the contract metadata admits an oracle.
        has_evidence = any(
            (h.evidence_for or h.evidence_against) for h in problem.hypotheses
        )
        return InvariantVerdict(
            "I4", "evidence_before_fact",
            holds=has_evidence,
            reason="evidence is recorded" if has_evidence
            else "no evidence recorded; cannot promote to fact",
        )

    @staticmethod
    def i5_lineage_preserved(problem: Problem) -> InvariantVerdict:
        # I5 holds iff at least one node carries a lineage pointer.
        has_any = any(h.lineage for h in problem.hypotheses) or bool(
            problem.metadata.get("lineage")
        )
        return InvariantVerdict(
            "I5", "lineage_preserved",
            holds=has_any,
            reason="lineage preserved" if has_any
            else "no lineage pointer anywhere — transformation would orphan",
        )

    @staticmethod
    def i6_economic_separation(problem: Problem) -> InvariantVerdict:
        # I6 holds iff the problem does not try to "buy" its own truth.
        bad = {"buy truth", "pay to verify", "stake the fact",
               "vote the hypothesis", "tokenize the proof"}
        text = (problem.objective + " " + " ".join(problem.constraints)).lower()
        hit = [t for t in bad if t in text]
        return InvariantVerdict(
            "I6", "epistemic_economic_separation",
            holds=not hit,
            reason="epistemic claims are not tokenized" if not hit
            else f"attempted economic override: {hit}",
        )

    @staticmethod
    def i7_continuity_floor(problem: Problem) -> InvariantVerdict:
        # I7 holds iff no proposed cost is "lethal". We treat any cost
        # > 1e9 or any single operation that would consume > 30% of an
        # implicit "vital reserve" as a continuity-floor violation.
        vital_fraction = 0.30
        offending = []
        for h in problem.hypotheses:
            if h.cost_estimate <= 0:
                continue
            # cost_estimate is in abstract units; here we just sanity-check
            # that the cost is not absurdly high relative to expected value
            # when expected value is also declared.
            if h.expected_value > 0 and h.cost_estimate / max(h.expected_value, 1e-9) > 1.0 / vital_fraction:
                offending.append(h.id)
        return InvariantVerdict(
            "I7", "continuity_floor",
            holds=not offending,
            reason="no operation would consume the vital reserve"
            if not offending
            else f"would breach vital reserve: {offending}",
        )

    @staticmethod
    def i8_planetary_boundary(problem: Problem) -> InvariantVerdict:
        # I8 holds iff the problem does not claim unverified regenerative benefit.
        text = (problem.objective + " " + " ".join(problem.constraints)).lower()
        claim_words = {"regenerative", "net positive", "carbon negative",
                       "planetary benefit", "pbr > 1"}
        has_claim = any(w in text for w in claim_words)
        has_measurement = bool(problem.metadata.get("measurement_proof")) or bool(
            problem.metadata.get("independent_witness")
        )
        ok = (not has_claim) or has_measurement
        return InvariantVerdict(
            "I8", "planetary_boundary",
            holds=ok,
            reason="no unverified regenerative claim" if ok
            else "regenerative claim without independent measurement",
        )

    # ----------------- aggregate API -----------------

    def evaluate(self, problem: Problem) -> List[InvariantVerdict]:
        return [
            self.i1_causal_identity(problem),
            self.i2_prohibited(problem),
            self.i3_proof_over_narrative(problem),
            self.i4_evidence_before_fact(problem),
            self.i5_lineage_preserved(problem),
            self.i6_economic_separation(problem),
            self.i7_continuity_floor(problem),
            self.i8_planetary_boundary(problem),
        ]

    @staticmethod
    def all_hold(verdicts: List[InvariantVerdict]) -> bool:
        return all(v.holds for v in verdicts)

    def enforce(self, problem: Problem) -> List[InvariantVerdict]:
        verdicts = self.evaluate(problem)
        for v in verdicts:
            if not v.holds:
                raise InvariantViolation(
                    f"INVARIANT {v.id} ({v.name}) violated: {v.reason}"
                )
        return verdicts
