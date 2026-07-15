"""Tests for Constitutional Laws and AXIS-8."""
import unittest
from matverse.schema import Problem, Hypothesis
from matverse.laws import ConstitutionalLaws
from matverse.axis8 import AXIS8


def _sample_problem() -> Problem:
    return Problem(
        id="P1",
        objective="Measure CLI adoption",
        scope="dev-tools",
        constraints=["must work offline"],
        stakeholders=["developers"],
        hypotheses=[
            Hypothesis(
                id="H1",
                claim="Offline CLI raises adoption",
                variables={"conversion": 0.05},
                evidence_for=["easy install", "deterministic"],
                evidence_against=["marketing is louder"],
                falsification_criteria="conversion < 0.02",
                test_method="monte_carlo",
                cost_estimate=20.0,
                expected_value=200.0,
                risk=0.2,
                reversibility=0.9,
                lineage=["v2.0.0"],
            )
        ],
        metadata={
            "science_origin": "Diffusion of Innovations (Rogers, 1962)",
            "contract": "yaml schema v3",
            "ecosystem_impact": "non-breaking",
        },
    )


class TestLaws(unittest.TestCase):

    def test_all_laws_evaluate(self):
        laws = ConstitutionalLaws()
        verdicts = laws.evaluate(_sample_problem())
        self.assertEqual(len(verdicts), 8)
        s = ConstitutionalLaws.summary(verdicts)
        self.assertEqual(s["total"], 8)
        self.assertEqual(s["holds"], 8)

    def test_missing_metadata_lowers_coherence(self):
        p = _sample_problem()
        p.metadata = {}
        p.hypotheses[0].lineage = []
        p.stakeholders = []
        laws = ConstitutionalLaws()
        verdicts = laws.evaluate(p)
        s = ConstitutionalLaws.summary(verdicts)
        self.assertLess(s["holds"], 8)
        self.assertGreater(s["missing"], 0)


class TestAxis8(unittest.TestCase):

    def test_all_lenses_fire(self):
        a = AXIS8()
        v = a.apply(_sample_problem().hypotheses[0])
        self.assertEqual({lv.lens for lv in v},
                         {"TRUTHMODE", "REDTEAM", "UNLEARN", "80/20",
                          "HORMOZI", "FUTUREYOU", "/human", "H-Axis"})

    def test_no_falsification_penalizes_truthmode(self):
        h = Hypothesis(id="Hx", claim="x", variables={"a": 1.0})
        v = {lv.lens: lv.score for lv in AXIS8().apply(h)}
        self.assertEqual(v["TRUTHMODE"], 0.0)

    def test_reversibility_penalizes_future_you(self):
        # risk: low reversibility => high future debt => low FUTUREYOU score
        h_low = Hypothesis(id="a", claim="x", variables={"a": 1.0},
                           cost_estimate=100, reversibility=0.0)
        h_hi = Hypothesis(id="b", claim="x", variables={"a": 1.0},
                          cost_estimate=100, reversibility=1.0)
        v_low = next(lv for lv in AXIS8().apply(h_low) if lv.lens == "FUTUREYOU")
        v_hi = next(lv for lv in AXIS8().apply(h_hi) if lv.lens == "FUTUREYOU")
        self.assertGreater(v_hi.score, v_low.score)


if __name__ == "__main__":
    unittest.main()
