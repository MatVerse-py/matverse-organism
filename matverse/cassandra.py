"""
matverse.cassandra
==================

Cassandra — the cognitive interpretation layer of the MatVerse organism.

Cassandra is NOT a LLM, an agent, or a chatbot. She is the composition
of:

    perception       (what is happening, from where, with what context)
  + interpretation   (which hypotheses compete, what would falsify each)
  + metacognition    (how did we arrive at this, what bias may be acting)
  + language         (how to express state without inflating possibility into fact)

She sits between MMNB (causal memory) and COG (capability composition).
Her output is a CassandraReading: a structured interpretation that
downstream organs (COG, UMJAM) can consume deterministically.

Cassandra never invents facts. She only structures what is already in
the MMNB and the active Problem.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .schema import Problem, Hypothesis
from .laws import ConstitutionalLaws
from .invariants import Invariants


@dataclass
class CassandraReading:
    problem_id: str
    classification: str                # OPEN | UNDERDETERMINED | INTRACTABLE | ...
    invariant_verdicts: List[Dict[str, Any]] = field(default_factory=list)
    law_verdicts: List[Dict[str, Any]] = field(default_factory=list)
    law_summary: Dict[str, Any] = field(default_factory=dict)
    invariant_summary: Dict[str, Any] = field(default_factory=dict)
    interpretation: str = ""
    competing_claims: List[Dict[str, Any]] = field(default_factory=list)
    candidate_falsifiers: List[Dict[str, Any]] = field(default_factory=list)
    metacognitive_notes: List[str] = field(default_factory=list)
    confidence_self_assessment: float = 0.0
    timestamp: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "classification": self.classification,
            "invariant_verdicts": self.invariant_verdicts,
            "law_verdicts": self.law_verdicts,
            "law_summary": self.law_summary,
            "invariant_summary": self.invariant_summary,
            "interpretation": self.interpretation,
            "competing_claims": self.competing_claims,
            "candidate_falsifiers": self.candidate_falsifiers,
            "metacognitive_notes": self.metacognitive_notes,
            "confidence_self_assessment": self.confidence_self_assessment,
            "timestamp": self.timestamp,
        }


class Cassandra:
    """The interpretive composition of perception, hypothesis, and metacognition."""

    def __init__(self, laws: Optional[ConstitutionalLaws] = None,
                 invariants: Optional[Invariants] = None) -> None:
        self.laws = laws or ConstitutionalLaws()
        self.invariants = invariants or Invariants()

    def interpret(self, problem: Problem,
                  classification: str = "OPEN_FOR_INVESTIGATION") -> CassandraReading:
        import time
        law_verdicts = self.laws.evaluate(problem)
        law_summary = self.laws.summary(law_verdicts)
        law_summary["verdicts"] = [v.to_dict() for v in law_verdicts]

        inv_verdicts = self.invariants.evaluate(problem)
        inv_summary = {
            "total": len(inv_verdicts),
            "holds": sum(1 for v in inv_verdicts if v.holds),
            "violated": [v.to_dict() for v in inv_verdicts if not v.holds],
        }

        # Interpretation string
        parts = [f"Problem {problem.id} classified as {classification}."]
        if inv_summary["violated"]:
            parts.append(
                f" {len(inv_summary['violated'])} invariant(s) violated: "
                + ", ".join(v["id"] for v in inv_summary["violated"])
            )
        else:
            parts.append(" All eight invariants hold.")
        parts.append(
            f" {law_summary['holds']}/{law_summary['total']} laws hold; "
            f"{law_summary['missing']} missing; {law_summary['failing']} failing."
        )
        interpretation = "".join(parts)

        # Competing claims: each hypothesis with its evidence
        competing = []
        for h in problem.hypotheses:
            competing.append({
                "id": h.id,
                "claim": h.claim,
                "evidence_for": h.evidence_for,
                "evidence_against": h.evidence_against,
                "falsification_criteria": h.falsification_criteria,
                "risk": h.risk,
                "reversibility": h.reversibility,
            })

        # Candidate falsifiers
        falsifiers = [
            {
                "hypothesis_id": h.id,
                "condition": h.falsification_criteria,
                "method": h.test_method,
            }
            for h in problem.hypotheses if h.falsification_criteria
        ]

        # Metacognitive notes — what could bias the reading?
        notes = []
        if not problem.hypotheses:
            notes.append("no competing claims: the field is empty")
        if all(len(h.evidence_against) == 0 for h in problem.hypotheses):
            notes.append("no counter-evidence recorded: risk of confirmation bias")
        if any(h.cost_estimate == 0 and h.expected_value > 0 for h in problem.hypotheses):
            notes.append("a zero-cost claim may be hiding a hidden cost")
        if law_summary["missing"] > 0:
            notes.append("missing laws indicate development requirements, not deletion")

        # Self-assessed confidence: high if all invariants hold + multiple claims
        if inv_summary["holds"] == inv_summary["total"] and len(problem.hypotheses) >= 2:
            confidence = 0.8
        elif inv_summary["holds"] == inv_summary["total"]:
            confidence = 0.5
        else:
            confidence = 0.2

        return CassandraReading(
            problem_id=problem.id,
            classification=classification,
            invariant_verdicts=[v.to_dict() for v in inv_verdicts],
            law_verdicts=[v.to_dict() for v in law_verdicts],
            law_summary=law_summary,
            invariant_summary=inv_summary,
            interpretation=interpretation,
            competing_claims=competing,
            candidate_falsifiers=falsifiers,
            metacognitive_notes=notes,
            confidence_self_assessment=confidence,
            timestamp=int(time.time()),
        )
