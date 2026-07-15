"""Tests for Cassandra (cognitive interpretation layer)."""
import unittest
from matverse.schema import Problem, Hypothesis
from matverse.cassandra import Cassandra


def _rich_problem() -> Problem:
    return Problem(
        id="P_RICH", objective="how to evaluate product X", scope="x",
        constraints=[], stakeholders=["a", "b"],
        hypotheses=[
            Hypothesis(id="H1", claim="claim1", variables={"v": 1.0},
                       evidence_for=["e1"], evidence_against=["c1"],
                       falsification_criteria="v < 0.5",
                       cost_estimate=10, expected_value=200,
                       risk=0.2, reversibility=0.9, lineage=["v3.0.0"]),
            Hypothesis(id="H2", claim="claim2", variables={"v": 0.3},
                       evidence_for=["e2"], evidence_against=["c2"],
                       falsification_criteria="v < 0.5",
                       cost_estimate=5, expected_value=100,
                       risk=0.4, reversibility=0.6, lineage=["v3.0.0"]),
        ],
        metadata={"science_origin": "x", "contract": "y",
                  "ecosystem_impact": "z", "lineage": ["v3.0.0"]},
    )


class TestCassandra(unittest.TestCase):

    def test_interpret_returns_reading(self):
        c = Cassandra()
        r = c.interpret(_rich_problem())
        self.assertEqual(r.problem_id, "P_RICH")
        self.assertEqual(len(r.competing_claims), 2)
        self.assertEqual(len(r.candidate_falsifiers), 2)
        self.assertIn("All eight invariants hold", r.interpretation)
        self.assertGreater(r.confidence_self_assessment, 0.5)

    def test_interpret_flags_no_evidence(self):
        p = _rich_problem()
        for h in p.hypotheses:
            h.evidence_for = []
            h.evidence_against = []
        r = Cassandra().interpret(p)
        self.assertTrue(any("confirmation bias" in n for n in r.metacognitive_notes))

    def test_interpret_flags_no_claims(self):
        p = _rich_problem()
        p.hypotheses = []
        r = Cassandra().interpret(p)
        self.assertTrue(any("empty" in n for n in r.metacognitive_notes))
        self.assertLess(r.confidence_self_assessment, 0.5)

    def test_interpret_includes_invariant_verdicts(self):
        r = Cassandra().interpret(_rich_problem())
        self.assertEqual(len(r.invariant_verdicts), 8)


if __name__ == "__main__":
    unittest.main()
