"""Tests for the Organism (Campo de Hipóteses)."""
import unittest
import os
import tempfile
from matverse.schema import Problem, Hypothesis
from matverse.organism import Organism, classify_problem
from matverse.ledger import Ledger


def _cli_problem() -> Problem:
    return Problem(
        id="P_CLI",
        objective="How to maximize CLI adoption on GitHub",
        scope="open-source dev tools",
        constraints=["works offline", "deterministic"],
        stakeholders=["developers", "DevRel"],
        hypotheses=[
            Hypothesis(
                id="H_OFFLINE",
                claim="An offline CLI increases first-week downloads",
                variables={"conversion_rate": 0.05},
                evidence_for=["no auth wall", "fast feedback loop"],
                evidence_against=["SaaS competitors have marketing"],
                falsification_criteria="conversion_rate < 0.02",
                test_method="monte_carlo",
                cost_estimate=20.0,
                expected_value=300.0,
                risk=0.2,
                reversibility=0.95,
                lineage=["v2.0.0"],
            ),
            Hypothesis(
                id="H_PROMISE",
                claim="Promising the product solves everything maximizes downloads",
                variables={"adoption_boost": 0.5},
                evidence_for=["viral headline potential"],
                evidence_against=["trust erosion"],
                falsification_criteria="adoption_boost < 0.05",
                test_method="monte_carlo",
                cost_estimate=10.0,
                expected_value=400.0,
                risk=0.6,
                reversibility=0.4,
                lineage=["v2.0.0"],
            ),
        ],
        metadata={
            "science_origin": "Diffusion of Innovations (Rogers, 1962)",
            "contract": "yaml schema v3",
            "ecosystem_impact": "additive, non-breaking",
        },
    )


class TestOrganism(unittest.TestCase):

    def test_classify_open(self):
        p = _cli_problem()
        self.assertEqual(classify_problem(p), "OPEN_FOR_INVESTIGATION")

    def test_classify_prohibited(self):
        p = Problem(id="P_BAD", objective="hack a server", scope="x", hypotheses=[])
        self.assertEqual(classify_problem(p), "PROHIBITED_ACTION")

    def test_investigate_returns_report(self):
        org = Organism(n_mc=200, seed=7)
        rep = org.investigate(_cli_problem())
        self.assertEqual(rep.problem_id, "P_CLI")
        self.assertEqual(rep.classification, "OPEN_FOR_INVESTIGATION")
        self.assertGreater(len(rep.ranked), 0)
        self.assertIn("decision", rep.to_dict())
        self.assertIsNotNone(rep.receipt_hash)

    def test_investigate_picks_higher_quality_hypothesis(self):
        # H_OFFLINE has lower risk and higher reversibility than H_PROMISE,
        # so it should rank first.
        org = Organism(n_mc=200, seed=7)
        rep = org.investigate(_cli_problem())
        top_id = rep.ranked[0]["id"]
        self.assertEqual(top_id, "H_OFFLINE")

    def test_ledger_persists_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "led.json")
            led = Ledger(path=path)
            org = Organism(ledger=led, n_mc=100, seed=1)
            org.investigate(_cli_problem())
            v = led.verify()
            self.assertTrue(v["ok"])
            self.assertEqual(v["length"], 1)

    def test_monte_carlo_records_cvar(self):
        org = Organism(n_mc=300, seed=1)
        rep = org.investigate(_cli_problem())
        self.assertIn("H_OFFLINE", rep.cvar)
        self.assertIn("H_OFFLINE", rep.monte_carlo)
        self.assertIn("H_OFFLINE", rep.threshold_prob)

    def test_sensitivity_is_present(self):
        org = Organism(n_mc=100, seed=1)
        rep = org.investigate(_cli_problem())
        self.assertIn("H_OFFLINE", rep.sensitivity)
        self.assertGreater(len(rep.sensitivity["H_OFFLINE"]), 0)


if __name__ == "__main__":
    unittest.main()
