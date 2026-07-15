"""
matverse.metacortex
===================

The Metacortex. The ninth organ. Watches the other eight.

Responsibility: aggregate LearningRecord entries, compute calibration error
per problem class, identify the best-performing strategies, and recommend a
method to apply to the next instance of a given problem class.

This is the implementation of level-3 learning: learning how the organism
learns, and using that to compress future effort.
"""
from __future__ import annotations
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .schema import LearningRecord
from .ledger import Ledger


@dataclass
class ClassProfile:
    problem_class: str
    n_records: int
    strategies: Dict[str, Dict[str, float]]  # strategy -> {mean_calibration, mean_time, pass_rate, n}
    recommended_strategy: Optional[str] = None
    recommendation_confidence: float = 0.0

    def to_dict(self) -> Dict[str, object]:
        return {
            "problem_class": self.problem_class,
            "n_records": self.n_records,
            "strategies": self.strategies,
            "recommended_strategy": self.recommended_strategy,
            "recommendation_confidence": self.recommendation_confidence,
        }


class Metacortex:
    """Aggregates learning records and produces per-class recommendations."""

    def __init__(self, ledger: Optional[Ledger] = None) -> None:
        self.ledger = ledger if ledger is not None else Ledger()
        self._records: List[LearningRecord] = []

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def record(self, rec: LearningRecord) -> None:
        self._records.append(rec)
        self.ledger.append(
            kind="metacortex", input_obj=rec.to_dict(),
            output_obj={"accepted": True}, status="RECORDED",
        )

    def load_records(self, records: List[Dict[str, object]]) -> int:
        accepted = 0
        for r in records:
            try:
                self._records.append(LearningRecord.from_dict(r))
                accepted += 1
            except (KeyError, TypeError):
                continue
        return accepted

    @property
    def records(self) -> List[LearningRecord]:
        return list(self._records)

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    def profile_by_class(self) -> Dict[str, ClassProfile]:
        by_class: Dict[str, Dict[str, List[LearningRecord]]] = defaultdict(lambda: defaultdict(list))
        for r in self._records:
            by_class[r.problem_class][r.strategy].append(r)

        profiles: Dict[str, ClassProfile] = {}
        for cls, by_strat in by_class.items():
            strat_profiles: Dict[str, Dict[str, float]] = {}
            for strat, recs in by_strat.items():
                cals = [r.calibration_error() for r in recs]
                times = [r.time_to_decision_s for r in recs]
                pass_rate = sum(1 for r in recs if r.outcome == "PASS") / max(1, len(recs))
                strat_profiles[strat] = {
                    "n": float(len(recs)),
                    "mean_calibration": round(statistics.fmean(cals), 4) if cals else 0.0,
                    "mean_time_s": round(statistics.fmean(times), 4) if times else 0.0,
                    "pass_rate": round(pass_rate, 4),
                }

            # Pick best strategy: maximize pass_rate, break ties with calibration
            best_strat: Optional[str] = None
            best_score: float = -math.inf
            for strat, p in strat_profiles.items():
                # Score = pass_rate * (1 - calibration)
                s = p["pass_rate"] * (1.0 - p["mean_calibration"])
                if s > best_score:
                    best_score = s
                    best_strat = strat

            total = sum(int(p["n"]) for p in strat_profiles.values())
            confidence = 0.0
            if best_strat and total > 0:
                # Confidence grows with sample size and dominance
                wins = int(strat_profiles[best_strat]["n"])
                confidence = min(1.0, wins / max(1, total) * (1.0 - 1.0 / max(1, total)))

            profiles[cls] = ClassProfile(
                problem_class=cls,
                n_records=total,
                strategies=strat_profiles,
                recommended_strategy=best_strat,
                recommendation_confidence=round(confidence, 3),
            )

        return profiles

    def recommend(self, problem_class: str) -> Optional[ClassProfile]:
        return self.profile_by_class().get(problem_class)

    def summary(self) -> Dict[str, object]:
        profiles = self.profile_by_class()
        return {
            "n_records": len(self._records),
            "n_classes": len(profiles),
            "classes": {cls: p.to_dict() for cls, p in profiles.items()},
        }
