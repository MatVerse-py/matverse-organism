"""Tests for the v3.7 probes and CLI commands."""
import unittest
import json
import os
import subprocess
import sys
import tempfile
from matverse.probes import (
    DeclaredProbe, RaplProbe, NvmlProbe, CompositeProbe,
    make_default_probe, ProbeMeasurement,
)
from matverse.thermo import DeclaredProbe as ThermoDeclared


REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _run(args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "matverse", *args],
        cwd=cwd or REPO, capture_output=True, text=True, timeout=60,
    )


class TestProbes(unittest.TestCase):

    def test_declared_probe_returns_workload(self):
        p = DeclaredProbe()
        e, co2, x = p.measure({"energy_wh": 1.0, "co2_g": 0.1, "exergy_wh": 0.8})
        self.assertEqual(e, 1.0)
        self.assertEqual(co2, 0.1)
        self.assertEqual(x, 0.8)

    def test_rapl_probe_falls_back_when_unavailable(self):
        p = RaplProbe()
        if p.available:
            e, _, _ = p.measure({"energy_wh": 5.0})
            self.assertGreaterEqual(e, 0.0)
        else:
            e, co2, x = p.measure({"energy_wh": 5.0, "co2_g": 0.5, "exergy_wh": 4.0})
            self.assertEqual(e, 5.0)

    def test_make_default_probe_returns_a_probe(self):
        p = make_default_probe()
        self.assertIsNotNone(p)

    def test_composite_probe_sums(self):
        p1 = DeclaredProbe()
        p2 = DeclaredProbe()
        c = CompositeProbe([p1, p2])
        e, co2, x = c.measure({"energy_wh": 1.0, "co2_g": 0.1, "exergy_wh": 0.8})
        self.assertEqual(e, 2.0)
        self.assertEqual(co2, 0.1)
        self.assertEqual(x, 1.6)

    def test_probe_measurement_to_workload(self):
        m = ProbeMeasurement(energy_wh=1.0, co2_g=0.1, exergy_wh=0.8, status="SENSOR")
        w = m.to_workload()
        self.assertEqual(w["measurement_status"], "SENSOR")
        self.assertEqual(w["energy_wh"], 1.0)


class TestCLIv3_7(unittest.TestCase):

    def test_invariants_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "prob.json")
            with open(inp, "w") as f:
                json.dump({
                    "id": "P", "objective": "x", "scope": "s",
                    "constraints": [], "stakeholders": ["t"],
                    "hypotheses": [{
                        "id": "H", "claim": "c", "variables": {"v": 1.0},
                        "evidence_for": ["e"], "evidence_against": ["c"],
                        "falsification_criteria": "v < 0.5",
                        "cost_estimate": 1, "expected_value": 10,
                        "risk": 0.2, "reversibility": 0.9,
                        "lineage": ["v3.0.0"],
                    }],
                    "metadata": {"science_origin": "x", "contract": "y",
                                 "ecosystem_impact": "z",
                                 "lineage": ["v3.0.0"]},
                }, f)
            r = _run(["invariants", "check", "-i", inp])
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            out = json.loads(r.stdout)
            self.assertTrue(out["all_hold"])

    def test_laws_evaluate(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "prob.json")
            with open(inp, "w") as f:
                json.dump({
                    "id": "P", "objective": "x", "scope": "s",
                    "constraints": [], "stakeholders": ["t"],
                    "hypotheses": [{
                        "id": "H", "claim": "c", "variables": {"v": 1.0},
                        "evidence_for": ["e"], "evidence_against": ["c"],
                        "falsification_criteria": "v < 0.5",
                        "cost_estimate": 1, "expected_value": 10,
                        "risk": 0.2, "reversibility": 0.9,
                        "lineage": ["v3.0.0"],
                    }],
                    "metadata": {"science_origin": "x", "contract": "y",
                                 "ecosystem_impact": "z",
                                 "lineage": ["v3.0.0"]},
                }, f)
            r = _run(["laws", "evaluate", "-i", inp])
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            out = json.loads(r.stdout)
            self.assertEqual(out["summary"]["total"], 8)

    def test_cassandra_interpret(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "prob.json")
            with open(inp, "w") as f:
                json.dump({
                    "id": "P", "objective": "x", "scope": "s",
                    "constraints": [], "stakeholders": ["t"],
                    "hypotheses": [{
                        "id": "H1", "claim": "c", "variables": {"v": 1.0},
                        "evidence_for": ["e"], "evidence_against": ["c"],
                        "falsification_criteria": "v < 0.5",
                        "cost_estimate": 1, "expected_value": 10,
                        "risk": 0.2, "reversibility": 0.9,
                        "lineage": ["v3.0.0"],
                    }],
                    "metadata": {"science_origin": "x", "contract": "y",
                                 "ecosystem_impact": "z",
                                 "lineage": ["v3.0.0"]},
                }, f)
            r = _run(["cassandra", "interpret", "-i", inp])
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            out = json.loads(r.stdout)
            self.assertEqual(out["problem_id"], "P")

    def test_atlas_health(self):
        r = _run(["atlas", "health"])
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        out = json.loads(r.stdout)
        self.assertIn("total_nodes", out)

    def test_thermo_report(self):
        r = _run(["thermo", "report"])
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        out = json.loads(r.stdout)
        self.assertIn("history_size", out)

    def test_captals_report(self):
        r = _run(["captals", "report"])
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        out = json.loads(r.stdout)
        self.assertIn("n_mbits", out)

    def test_existential_status(self):
        r = _run(["existential", "status"])
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        out = json.loads(r.stdout)
        self.assertIn("apoptosis", out)
        self.assertIn("antifragility", out)

    def test_mmnb_show(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = os.path.join(tmp, "mmnb")
            r = _run(["mmnb", "show", "--store", store])
            # No MMNB yet; rc should be 1
            self.assertEqual(r.returncode, 1)

    def test_organism_run_subcommand(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "prob.json")
            with open(inp, "w") as f:
                json.dump({
                    "id": "P_ORG", "objective": "x", "scope": "s",
                    "constraints": [], "stakeholders": ["t"],
                    "hypotheses": [{
                        "id": "H", "claim": "c", "variables": {"v": 1.0},
                        "evidence_for": ["e"], "evidence_against": ["c"],
                        "falsification_criteria": "v < 0.5",
                        "cost_estimate": 1, "expected_value": 10,
                        "risk": 0.2, "reversibility": 0.9,
                        "lineage": ["v3.0.0"],
                    }],
                    "metadata": {"science_origin": "x", "contract": "y",
                                 "ecosystem_impact": "z",
                                 "lineage": ["v3.0.0"]},
                }, f)
            out = os.path.join(tmp, "closure.json")
            r = _run(["organism", "run", "-i", inp, "-o", out])
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            with open(out) as f:
                data = json.load(f)
            self.assertIn("closure", data)
            self.assertTrue(data["closure"]["state_closure"]
                            in ("CLOSED", "REPLAYED_INDEPENDENT"))

    def test_publish_prepare(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "prob.json")
            with open(inp, "w") as f:
                json.dump({
                    "id": "P", "objective": "x", "scope": "s",
                    "constraints": [], "stakeholders": ["t"],
                    "hypotheses": [{
                        "id": "H", "claim": "c", "variables": {"v": 1.0},
                        "evidence_for": ["e"], "evidence_against": ["c"],
                        "falsification_criteria": "v < 0.5",
                        "cost_estimate": 1, "expected_value": 10,
                        "risk": 0.2, "reversibility": 0.9,
                        "lineage": ["v3.0.0"],
                    }],
                    "metadata": {"science_origin": "x", "contract": "y",
                                 "ecosystem_impact": "z",
                                 "lineage": ["v3.0.0"]},
                }, f)
            closure_out = os.path.join(tmp, "closure.json")
            r1 = _run(["organism", "run", "-i", inp, "-o", closure_out])
            self.assertEqual(r1.returncode, 0, msg=r1.stderr)
            pub_out = os.path.join(tmp, "publication.json")
            r2 = _run(["publish", "prepare", "-i", closure_out,
                       "--repository", "MatVerse-py/matverse-organism",
                       "-o", pub_out])
            self.assertEqual(r2.returncode, 0, msg=r2.stderr)
            with open(pub_out) as f:
                pub = json.load(f)
            self.assertEqual(pub["zenodo"]["status"], "PREPARED_NOT_PUBLISHED")
            self.assertEqual(pub["github"]["status"], "PREPARED_NOT_RELEASED")
            self.assertEqual(pub["huggingface"]["status"],
                             "PREPARED_NOT_PUBLISHED")
            self.assertEqual(pub["blockchain"]["status"],
                             "PREPARED_NOT_BROADCAST")


if __name__ == "__main__":
    unittest.main()
