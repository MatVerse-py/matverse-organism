"""Tests for the Invariants engine."""
import unittest
from matverse.schema import Problem, Hypothesis
from matverse.invariants import Invariants, InvariantViolation


def _ok_problem() -> Problem:
    return Problem(
        id="P_OK", objective="how to test invariants", scope="x",
        constraints=[], stakeholders=["tester"],
        hypotheses=[Hypothesis(
            id="H_OK", claim="c", variables={"a": 1.0},
            evidence_for=["e1"], evidence_against=["e2"],
            falsification_criteria="a < 0.5",
            cost_estimate=10.0, expected_value=100.0,
            risk=0.2, reversibility=0.9,
            lineage=["v3.0.0"],
        )],
        metadata={
            "science_origin": "x", "contract": "y", "ecosystem_impact": "z",
            "lineage": ["v3.0.0"],
        },
    )


def _prohibited_problem() -> Problem:
    p = _ok_problem()
    p.objective = "exploit a server"
    return p


class TestInvariants(unittest.TestCase):

    def test_all_eight_invariants_evaluated(self):
        v = Invariants().evaluate(_ok_problem())
        ids = [x.id for x in v]
        self.assertEqual(len(ids), 8)
        self.assertEqual(set(ids),
                         {"I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8"})

    def test_ok_problem_passes_all_invariants(self):
        self.assertTrue(Invariants.all_hold(Invariants().evaluate(_ok_problem())))

    def test_prohibited_problem_fails_i2(self):
        v = Invariants().evaluate(_prohibited_problem())
        ids = {x.id for x in v if not x.holds}
        self.assertIn("I2", ids)

    def test_no_falsification_fails_i3(self):
        p = _ok_problem()
        p.hypotheses[0].falsification_criteria = ""
        v = Invariants().evaluate(p)
        self.assertIn("I3", {x.id for x in v if not x.holds})

    def test_no_evidence_fails_i4(self):
        p = _ok_problem()
        p.hypotheses[0].evidence_for = []
        p.hypotheses[0].evidence_against = []
        v = Invariants().evaluate(p)
        self.assertIn("I4", {x.id for x in v if not x.holds})

    def test_no_lineage_fails_i1_and_i5(self):
        p = _ok_problem()
        p.hypotheses[0].lineage = []
        if "lineage" in p.metadata:
            del p.metadata["lineage"]
        v = Invariants().evaluate(p)
        bad = {x.id for x in v if not x.holds}
        self.assertIn("I1", bad)
        self.assertIn("I5", bad)

    def test_enforce_raises_on_violation(self):
        with self.assertRaises(InvariantViolation):
            Invariants().enforce(_prohibited_problem())

    def test_enforce_passes_on_clean_problem(self):
        Invariants().enforce(_ok_problem())  # should not raise


if __name__ == "__main__":
    unittest.main()
