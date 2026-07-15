"""Tests for the URANO Metabolic Runtime."""
import unittest
from matverse.urano import URANO
from matverse.organism import Organism
from matverse.closure import ClosureCompiler
from matverse.schema import Problem, Hypothesis
from matverse.ledger import Ledger


def _simple_problem() -> Problem:
    return Problem(
        id="P_SIMPLE",
        objective="Will a deterministic seed produce reproducible results?",
        scope="test",
        constraints=[],
        stakeholders=["tester"],
        hypotheses=[
            Hypothesis(
                id="H_REPRO",
                claim="Seed=42 always gives mean=1.0",
                variables={"value": 1.0},
                evidence_for=["determinism"],
                evidence_against=[],
                falsification_criteria="value < 0.5",
                test_method="monte_carlo",
                cost_estimate=1.0,
                expected_value=10.0,
                risk=0.1,
                reversibility=1.0,
                lineage=["v2.0.0"],
            )
        ],
        metadata={
            "science_origin": "PRNG theory",
            "contract": "executor-contract-v3",
            "ecosystem_impact": "none",
        },
    )


class TestURANO(unittest.TestCase):

    def test_compile_produces_contract(self):
        urano = URANO()
        c = urano.compile(
            problem_id="P_SIMPLE", hypothesis_id="H_REPRO",
            claim="seed reproducible", falsification="value < 0.5",
            test_method="monte_carlo", seed=42,
        )
        self.assertEqual(c.problem_id, "P_SIMPLE")
        self.assertEqual(c.seed, 42)
        self.assertEqual(c.network, "denied")
        self.assertEqual(c.executor_mode, "local_sandbox")

    def test_run_passes_with_good_claim(self):
        urano = URANO()
        c = urano.compile("P", "H", "c", "value < 0.5", "monte_carlo", seed=1,
                          inputs={"n_samples": 200, "mu": 1.0, "sigma": 0.1})
        r = urano.run(c)
        self.assertEqual(r.status, "PASS")
        self.assertFalse(r.refuted)
        self.assertIn("summary", r.observation)

    def test_run_refutes_with_bad_claim(self):
        urano = URANO()
        c = urano.compile("P", "H", "c", "value < 0.5", "monte_carlo", seed=1,
                          inputs={"n_samples": 200, "mu": 0.1, "sigma": 0.01})
        r = urano.run(c)
        self.assertTrue(r.refuted)
        self.assertEqual(r.status, "REFUTED_PRESERVED")


class TestClosure(unittest.TestCase):

    def test_full_cycle_closes(self):
        led = Ledger()
        org = Organism(ledger=led, n_mc=300, seed=1)
        urano = URANO(ledger=led)
        closure = ClosureCompiler(org, urano, ledger=led)
        rep = closure.run_full_cycle(_simple_problem(), seed=1, auto_execute=True)
        self.assertTrue(rep.closed)
        steps = {s["step"] for s in rep.steps}
        self.assertIn("investigate", steps)
        self.assertIn("compile", steps)
        self.assertIn("run", steps)

    def test_compile_only_when_auto_execute_false(self):
        led = Ledger()
        org = Organism(ledger=led, n_mc=200, seed=1)
        urano = URANO(ledger=led)
        closure = ClosureCompiler(org, urano, ledger=led)
        rep = closure.run_full_cycle(_simple_problem(), auto_execute=False)
        self.assertFalse(rep.closed)
        self.assertIn("auto_execute=False: experiment compiled but not run", rep.missing)


if __name__ == "__main__":
    unittest.main()
