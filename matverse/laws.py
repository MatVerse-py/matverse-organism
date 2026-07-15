"""
matverse.laws
=============

The 8 Constitutional Laws of MatVerse. They are NOT magic mantras; they are
verifiable lineage conditions applied to a Problem/Hypothesis graph.

A law either holds, is missing (which becomes a development requirement), or
fails. A failure is recorded; the node is not deleted — it is preserved with
its lineage so the system can learn from it.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Any

from .schema import Problem, Hypothesis


@dataclass
class LawVerdict:
    law_id: str
    name: str
    holds: bool
    missing: bool
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "law_id": self.law_id,
            "name": self.name,
            "holds": self.holds,
            "missing": self.missing,
            "notes": self.notes,
        }


class ConstitutionalLaws:
    """8 Constitutional Laws.

    A law is 'missing' when its precondition cannot be evaluated. A missing
    law is a development requirement, not a deletion trigger.
    """

    LAW_1 = ("LW1", "phenomenon_origin",
             "No science without a phenomenon (problem must name a phenomenon).")
    LAW_2 = ("LW2", "experiment_link",
             "No claim without an experiment pathway.")
    LAW_3 = ("LW3", "science_origin",
             "No engineering without an upstream scientific basis.")
    LAW_4 = ("LW4", "contract",
             "No artifact without a contract (interface / schema).")
    LAW_5 = ("LW5", "product_value",
             "No product without observable value to a stakeholder.")
    LAW_6 = ("LW6", "service_safety",
             "No service without a reversibility plan.")
    LAW_7 = ("LW7", "heritage",
             "No evolution without a recorded lineage of predecessors.")
    LAW_8 = ("LW8", "ecosystem_impact",
             "No deployment without an ecosystem-impact statement.")

    ALL = [LAW_1, LAW_2, LAW_3, LAW_4, LAW_5, LAW_6, LAW_7, LAW_8]

    def evaluate(self, problem: Problem) -> List[LawVerdict]:
        verdicts: List[LawVerdict] = []

        # LW1 — phenomenon
        if problem.objective.strip():
            verdicts.append(LawVerdict(self.LAW_1[0], self.LAW_1[1], True, False,
                                      "objective names a phenomenon."))
        else:
            verdicts.append(LawVerdict(self.LAW_1[0], self.LAW_1[1], False, True,
                                      "objective is empty; require phenomenon."))

        # LW2 — experiment pathway
        if not problem.hypotheses:
            verdicts.append(LawVerdict(self.LAW_2[0], self.LAW_2[1], False, True,
                                      "no hypotheses; require experiment pathway."))
        else:
            all_have_path = all(h.test_method and h.falsification_criteria for h in problem.hypotheses)
            verdicts.append(LawVerdict(self.LAW_2[0], self.LAW_2[1], all_have_path, False,
                                      "experiment pathway present." if all_have_path else
                                      "at least one hypothesis lacks test_method or falsification."))

        # LW3 — science origin
        has_origin = bool(problem.metadata.get("science_origin"))
        verdicts.append(LawVerdict(self.LAW_3[0], self.LAW_3[1], has_origin, not has_origin,
                                  "science_origin metadata present." if has_origin else
                                  "no science_origin; provide at least one reference (paper/DOI/field)."))

        # LW4 — contract
        has_contract = bool(problem.metadata.get("contract"))
        verdicts.append(LawVerdict(self.LAW_4[0], self.LAW_4[1], has_contract, not has_contract,
                                  "contract metadata present." if has_contract else
                                  "no contract; provide a schema or interface description."))

        # LW5 — product value
        has_value = bool(problem.stakeholders) and any(h.expected_value > 0 for h in problem.hypotheses)
        verdicts.append(LawVerdict(self.LAW_5[0], self.LAW_5[1], has_value, not has_value,
                                  "stakeholders + expected_value present." if has_value else
                                  "no observable stakeholder value declared."))

        # LW6 — service safety
        safe = all(h.reversibility >= 0.5 for h in problem.hypotheses) if problem.hypotheses else False
        verdicts.append(LawVerdict(self.LAW_6[0], self.LAW_6[1], safe, not safe and not problem.hypotheses,
                                  "reversibility ≥ 0.5 on all hypotheses." if safe else
                                  "some hypothesis has irreversibility ≥ 0.5; require explicit rollback."))

        # LW7 — heritage
        has_lineage = any(h.lineage for h in problem.hypotheses) or "lineage" in problem.metadata
        verdicts.append(LawVerdict(self.LAW_7[0], self.LAW_7[1], has_lineage, not has_lineage,
                                  "lineage recorded." if has_lineage else
                                  "no lineage; record at least one predecessor."))

        # LW8 — ecosystem impact
        has_impact = bool(problem.metadata.get("ecosystem_impact"))
        verdicts.append(LawVerdict(self.LAW_8[0], self.LAW_8[1], has_impact, not has_impact,
                                  "ecosystem_impact declared." if has_impact else
                                  "no ecosystem_impact statement; describe external effects."))

        return verdicts

    @staticmethod
    def summary(verdicts: List[LawVerdict]) -> Dict[str, Any]:
        total = len(verdicts)
        holds = sum(1 for v in verdicts if v.holds)
        missing = sum(1 for v in verdicts if v.missing and not v.holds)
        failing = sum(1 for v in verdicts if (not v.holds) and (not v.missing))
        return {
            "total": total,
            "holds": holds,
            "missing": missing,
            "failing": failing,
            "coherence": (holds / total) if total else 0.0,
        }
