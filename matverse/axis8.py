"""
matverse.axis8
==============

AXIS-8 analytical lenses. Each lens exposes a specific kind of weakness in a
hypothesis. Lenses do NOT prove or refute; they reveal where the hypothesis is
strong, weak, or incomplete.

  TRUTHMODE  — anti-self-deception; separates observation from interpretation
  REDTEAM    — finds counter-arguments and adversarial framings
  UNLEARN    — defines when to abandon or revise the hypothesis
  80/20      — finds the highest-leverage next test
  HORMOZI    — demands observable value to a named stakeholder
  FUTUREYOU  — measures future debt and lock-in cost
  /human     — protects autonomy and human impact
  H-Axis     — separates narrative from evidence (hype vs data)
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Any

from .schema import Hypothesis


@dataclass
class LensVerdict:
    lens: str
    score: float          # 0.0 to 1.0
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {"lens": self.lens, "score": self.score, "notes": self.notes}


class AXIS8:
    LENSES = [
        "TRUTHMODE", "REDTEAM", "UNLEARN", "80/20",
        "HORMOZI", "FUTUREYOU", "/human", "H-Axis",
    ]

    def apply(self, h: Hypothesis) -> List[LensVerdict]:
        out: List[LensVerdict] = []
        out.append(self._truthmode(h))
        out.append(self._redteam(h))
        out.append(self._unlearn(h))
        out.append(self._eighty_twenty(h))
        out.append(self._hormozi(h))
        out.append(self._future_you(h))
        out.append(self._human(h))
        out.append(self._h_axis(h))
        return out

    @staticmethod
    def _truthmode(h: Hypothesis) -> LensVerdict:
        # Penalize if no falsification criteria
        score = 1.0 if h.falsification_criteria else 0.0
        return LensVerdict("TRUTHMODE", score,
                           "falsification criteria explicit" if score else
                           "no falsification criteria — cannot distinguish belief from fact")

    @staticmethod
    def _redteam(h: Hypothesis) -> LensVerdict:
        # Reward explicit counter-evidence
        score = min(1.0, 0.3 + 0.7 * min(3, len(h.evidence_against)) / 3.0)
        return LensVerdict("REDTEAM", score,
                           f"{len(h.evidence_against)} counter-argument(s) on record")

    @staticmethod
    def _unlearn(h: Hypothesis) -> LensVerdict:
        # If reversibility is high AND falsification is explicit, easy to abandon
        score = 0.4 * h.reversibility + 0.6 * (1.0 if h.falsification_criteria else 0.0)
        return LensVerdict("UNLEARN", round(score, 3),
                           f"reversibility={h.reversibility:.2f}, "
                           f"falsifiable={bool(h.falsification_criteria)}")

    @staticmethod
    def _eighty_twenty(h: Hypothesis) -> LensVerdict:
        # Test cost vs expected value; reward when EV >> cost
        if h.cost_estimate <= 0:
            score = 0.5
        else:
            ratio = h.expected_value / h.cost_estimate
            score = min(1.0, ratio / 10.0)
        return LensVerdict("80/20", round(score, 3),
                           f"EV/cost ratio = {h.expected_value / max(h.cost_estimate, 1e-9):.2f}")

    @staticmethod
    def _hormozi(h: Hypothesis) -> LensVerdict:
        # Demand observable value: explicit metrics?
        score = 1.0 if h.expected_value > 0 else 0.0
        return LensVerdict("HORMOZI", score,
                           "value is quantified" if score else
                           "no observable value declaration")

    @staticmethod
    def _future_you(h: Hypothesis) -> LensVerdict:
        # Future debt = (1 - reversibility) * cost
        debt = (1.0 - h.reversibility) * h.cost_estimate
        score = max(0.0, 1.0 - debt / 100.0)
        return LensVerdict("FUTUREYOU", round(score, 3),
                           f"estimated future debt = {debt:.2f}")

    @staticmethod
    def _human(h: Hypothesis) -> LensVerdict:
        # Treat risk as proxy for human impact (lower risk => higher score)
        score = max(0.0, 1.0 - h.risk)
        return LensVerdict("/human", round(score, 3),
                           f"risk={h.risk:.2f}; lower risk = higher score")

    @staticmethod
    def _h_axis(h: Hypothesis) -> LensVerdict:
        # Evidence asymmetry: if much more 'for' than 'against' or vice-versa, score down
        total = len(h.evidence_for) + len(h.evidence_against)
        if total == 0:
            return LensVerdict("H-Axis", 0.0, "no evidence at all")
        diff = abs(len(h.evidence_for) - len(h.evidence_against)) / total
        score = 1.0 - diff
        return LensVerdict("H-Axis", round(score, 3),
                           f"evidence_for={len(h.evidence_for)}, "
                           f"evidence_against={len(h.evidence_against)}")

    @staticmethod
    def aggregate(verdicts: List[LensVerdict]) -> Dict[str, Any]:
        if not verdicts:
            return {"mean": 0.0, "lenses": {}}
        m = sum(v.score for v in verdicts) / len(verdicts)
        return {"mean": round(m, 3),
                "lenses": {v.lens: v.score for v in verdicts}}
