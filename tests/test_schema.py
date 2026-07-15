"""Tests for the schema module (data contracts)."""
import unittest
from matverse.schema import Problem, Hypothesis, LearningRecord, ExperimentResult


class TestSchema(unittest.TestCase):

    def test_problem_roundtrip(self):
        p = Problem(
            id="P1",
            objective="x",
            scope="y",
            constraints=["a"],
            stakeholders=["s1"],
            hypotheses=[Hypothesis(id="H1", claim="c", variables={"k": 1.0})],
            metadata={"k": "v"},
        )
        d = p.to_dict()
        p2 = Problem.from_dict(d)
        self.assertEqual(p2.id, p.id)
        self.assertEqual(p2.hypotheses[0].id, "H1")

    def test_hypothesis_unknown_keys_dropped(self):
        h = Hypothesis.from_dict({
            "id": "H1", "claim": "c",
            "this_key_does_not_exist": "ignored",
        })
        self.assertEqual(h.id, "H1")
        self.assertFalse(hasattr(h, "this_key_does_not_exist"))

    def test_experiment_result_roundtrip(self):
        r = ExperimentResult(
            experiment_id="E1", hypothesis_id="H1", status="PASS",
            observation={"mean": 1.0}, duration_s=0.1,
        )
        d = r.to_dict()
        r2 = ExperimentResult.from_dict(d)
        self.assertEqual(r2.experiment_id, "E1")

    def test_learning_record_calibration(self):
        rec = LearningRecord(
            timestamp=0, problem_class="x", strategy="y",
            lenses_used=[], monte_carlo_n=1, seed=0,
            outcome="PASS", time_to_decision_s=1.0,
            predicted_probability=0.7, observed_outcome_value=1.0,
        )
        # PASS target = 1.0
        self.assertAlmostEqual(rec.calibration_error(), 0.3, places=3)


if __name__ == "__main__":
    unittest.main()
