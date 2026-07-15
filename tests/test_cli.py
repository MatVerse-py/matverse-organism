"""End-to-end CLI tests using subprocess."""
import unittest
import json
import os
import subprocess
import sys
import tempfile


REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _run(cmd):
    return subprocess.run(
        [sys.executable, "-m", "matverse", *cmd],
        cwd=REPO, capture_output=True, text=True, timeout=60,
    )


class TestCLI(unittest.TestCase):

    def test_init_creates_problem_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "prob.json")
            r = _run(["init", "--objective", "Test objective",
                      "--n-hypotheses", "2", "-o", out])
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            self.assertTrue(os.path.exists(out))
            with open(out) as f:
                data = json.load(f)
            self.assertEqual(data["objective"], "Test objective")
            self.assertEqual(len(data["hypotheses"]), 2)

    def test_resolve_organism_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "prob.json")
            with open(inp, "w") as f:
                json.dump({
                    "id": "P", "objective": "obj", "scope": "s",
                    "constraints": [], "stakeholders": ["x"],
                    "hypotheses": [{
                        "id": "H", "claim": "c",
                        "variables": {"v": 1.0},
                        "evidence_for": [], "evidence_against": [],
                        "falsification_criteria": "v < 0.5",
                        "test_method": "monte_carlo",
                        "cost_estimate": 10, "expected_value": 50,
                        "risk": 0.2, "reversibility": 0.9,
                        "lineage": [],
                    }],
                    "metadata": {
                        "science_origin": "x", "contract": "y",
                        "ecosystem_impact": "z",
                    },
                }, f)
            r = _run(["resolve", "-i", inp, "--n-mc", "100"])
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            out = json.loads(r.stdout)
            self.assertIn("organism_report", out)
            self.assertIn("ledger_verification", out)

    def test_resolve_full_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "prob.json")
            with open(inp, "w") as f:
                json.dump({
                    "id": "P", "objective": "obj", "scope": "s",
                    "constraints": [], "stakeholders": ["x"],
                    "hypotheses": [{
                        "id": "H", "claim": "c",
                        "variables": {"v": 1.0},
                        "evidence_for": [], "evidence_against": [],
                        "falsification_criteria": "v < 0.5",
                        "test_method": "monte_carlo",
                        "cost_estimate": 10, "expected_value": 50,
                        "risk": 0.2, "reversibility": 0.9,
                        "lineage": [],
                    }],
                    "metadata": {
                        "science_origin": "x", "contract": "y",
                        "ecosystem_impact": "z",
                    },
                }, f)
            out = os.path.join(tmp, "out.json")
            r = _run(["resolve", "-i", inp, "--execute", "-o", out, "--n-mc", "100"])
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            with open(out) as f:
                data = json.load(f)
            self.assertTrue(data["closure_report"]["closed"])

    def test_promote_records_and_recommends(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "meta.json")
            r = _run([
                "promote",
                "--problem-class", "CLI_adoption",
                "--strategy", "concrete_first",
                "--lenses", "TRUTHMODE,80/20",
                "--outcome", "PASS",
                "--predicted", "0.85",
                "--observed", "1.0",
                "--time", "1.2",
                "-o", out,
            ])
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            with open(out) as f:
                data = json.load(f)
            self.assertEqual(data["recorded"]["problem_class"], "CLI_adoption")
            self.assertIsNotNone(data["recommendation"])


if __name__ == "__main__":
    unittest.main()
