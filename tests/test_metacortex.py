"""Tests for the Metacortex (level-3 learning)."""
import unittest
import time
from matverse.metacortex import Metacortex
from matverse.schema import LearningRecord


def _rec(cls, strat, outcome, predicted, observed, t=1.0, lenses=None):
    return LearningRecord(
        timestamp=int(time.time()),
        problem_class=cls,
        strategy=strat,
        lenses_used=lenses or ["TRUTHMODE", "80/20"],
        monte_carlo_n=5000,
        seed=0,
        outcome=outcome,
        time_to_decision_s=t,
        predicted_probability=predicted,
        observed_outcome_value=observed,
    )


class TestMetacortex(unittest.TestCase):

    def test_empty_summary(self):
        m = Metacortex()
        s = m.summary()
        self.assertEqual(s["n_records"], 0)
        self.assertEqual(s["n_classes"], 0)

    def test_records_calibration_error(self):
        r = _rec("CLI", "concrete_first", "PASS", predicted=0.9, observed=1.0)
        # predicted 0.9 vs target 1.0 (PASS) => 0.1
        self.assertAlmostEqual(r.calibration_error(), 0.1, places=3)

    def test_recommends_best_strategy(self):
        m = Metacortex()
        for _ in range(5):
            m.record(_rec("CLI", "concrete_first", "PASS", 0.85, 1.0, t=1.0))
        for _ in range(5):
            m.record(_rec("CLI", "vague_promise", "REFUTED_PRESERVED", 0.5, 0.0, t=2.0))
        prof = m.recommend("CLI")
        self.assertIsNotNone(prof)
        self.assertEqual(prof.recommended_strategy, "concrete_first")
        self.assertGreater(prof.n_records, 0)

    def test_load_records(self):
        m = Metacortex()
        recs = [_rec("A", "s1", "PASS", 0.8, 1.0).to_dict() for _ in range(3)]
        n = m.load_records(recs)
        self.assertEqual(n, 3)
        self.assertEqual(len(m.records), 3)


if __name__ == "__main__":
    unittest.main()
