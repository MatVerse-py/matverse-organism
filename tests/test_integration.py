"""Top-level integration test: a full cognitive cycle runs end-to-end."""
import unittest
import tempfile
import os
from matverse import (
    Organism, URANO, ClosureCompiler, Metacortex, Ledger,
    Problem, Hypothesis, LearningRecord,
)
from matverse.seeds import SEED_V3_2026_07_14


def _full_problem() -> Problem:
    return Problem(
        id="P_FULL",
        objective="Adoption of a deterministic CLI for code review",
        scope="github",
        constraints=["offline", "deterministic"],
        stakeholders=["maintainers", "contributors"],
        hypotheses=[
            Hypothesis(
                id="H_OFFLINE",
                claim="Offline CLI doubles first-week adoption",
                variables={"adoption_uplift": 2.0},
                evidence_for=["no auth", "fast feedback"],
                evidence_against=["marketing is louder"],
                falsification_criteria="adoption_uplift < 1.2",
                test_method="monte_carlo",
                cost_estimate=20.0, expected_value=500.0,
                risk=0.2, reversibility=0.95,
                lineage=["v2.0.0"],
            ),
            Hypothesis(
                id="H_PROMISE",
                claim="Universal solver promise maximizes downloads",
                variables={"adoption_uplift": 5.0},
                evidence_for=["headline potential"],
                evidence_against=["trust erosion", "scope risk"],
                falsification_criteria="adoption_uplift < 1.2",
                test_method="monte_carlo",
                cost_estimate=10.0, expected_value=800.0,
                risk=0.7, reversibility=0.3,
                lineage=["v2.0.0"],
            ),
        ],
        metadata={
            "science_origin": "Diffusion of Innovations (Rogers, 1962)",
            "contract": "schema/v3/problem.schema.json",
            "ecosystem_impact": "additive, opt-in",
        },
    )


class TestFullIntegration(unittest.TestCase):

    def test_full_cycle_with_metacortex_feedback(self):
        with tempfile.TemporaryDirectory() as tmp:
            led_path = os.path.join(tmp, "led.json")
            ledger = Ledger(path=led_path)
            org = Organism(ledger=ledger, n_mc=500, seed=SEED_V3_2026_07_14["issued_at"])
            urano = URANO(ledger=ledger)
            closure = ClosureCompiler(org, urano, ledger=ledger)
            mc = Metacortex(ledger=ledger)

            rep = closure.run_full_cycle(_full_problem(),
                                         seed=SEED_V3_2026_07_14["issued_at"],
                                         auto_execute=True)

            # Cycle should be closed
            self.assertTrue(rep.closed)
            # Top hypothesis should be the safer, more reversible one
            org_report = org.investigate(_full_problem())
            self.assertEqual(org_report.ranked[0]["id"], "H_OFFLINE")

            # Now feed the Metacortex
            lr = LearningRecord(
                timestamp=ledger.entries()[-1].timestamp,
                problem_class="CLI_adoption",
                strategy="concrete_first",
                lenses_used=["TRUTHMODE", "REDTEAM", "80/20"],
                monte_carlo_n=500,
                seed=SEED_V3_2026_07_14["issued_at"],
                outcome=org_report.decision,
                time_to_decision_s=0.1,
                predicted_probability=0.85,
                observed_outcome_value=1.0,
            )
            mc.record(lr)
            summary = mc.summary()
            self.assertEqual(summary["n_records"], 1)

            # Ledger verifies
            v = ledger.verify()
            self.assertTrue(v["ok"])
            self.assertGreater(v["length"], 0)

    def test_prohibited_problem_halted_at_gate(self):
        ledger = Ledger()
        org = Organism(ledger=ledger, n_mc=100, seed=1)
        p = Problem(
            id="P_BAD",
            objective="hack a server remotely",
            scope="x",
            constraints=[],
            stakeholders=[],
            hypotheses=[Hypothesis(id="H", claim="do it", variables={"x": 1.0})],
        )
        rep = org.investigate(p)
        self.assertEqual(rep.classification, "PROHIBITED_ACTION")
        self.assertEqual(rep.decision, "PROHIBITED_ACTION")


if __name__ == "__main__":
    unittest.main()
