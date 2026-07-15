"""Tests for the v3.6 closure macro, publications, and replay."""
import unittest
import os
import tempfile
from matverse.organism import Organism
from matverse.umjam import UMJAM, UMJAMSpec
from matverse.svca import SVCA
from matverse.thermo import ThermoCortex
from matverse.captals import MBit
from matverse.closure_macro import (
    ClosureMacroCompiler, _merkle,
)
from matverse.publishers import (
    prepare_publication, zenodo_metadata, github_release_metadata,
    huggingface_metadata, blockchain_anchor,
)
from matverse.replay import Replayer


def _simple_problem_dict() -> dict:
    return {
        "id": "P_R1", "objective": "x", "scope": "s",
        "constraints": [], "stakeholders": ["t"],
        "hypotheses": [{
            "id": "H1", "claim": "c", "variables": {"v": 1.0},
            "evidence_for": ["e"], "evidence_against": [],
            "falsification_criteria": "v < 0.5",
            "test_method": "monte_carlo",
            "cost_estimate": 1.0, "expected_value": 10.0,
            "risk": 0.1, "reversibility": 0.9,
            "lineage": ["v3.0.0"],
        }],
        "metadata": {"science_origin": "x", "contract": "y",
                     "ecosystem_impact": "z", "lineage": ["v3.0.0"]},
    }


def _svca() -> SVCA:
    umjam = UMJAM()
    spec = UMJAMSpec(operation_id="OP1", capability_id="echo.v1",
                     inputs={"a": 1}, seed=42, purpose="test")
    r = umjam.transmute(spec, {"a": 1})
    return SVCA.from_transmutation(spec, r, metrics={"x": 1})


def _thermo():
    tc = ThermoCortex()
    return tc.record("EX1", {
        "energy_wh": 1.0, "co2_g": 0.1, "exergy_wh": 0.8,
        "external_energy_avoided_wh": 5.0,
        "heat_recovered_wh": 0.1,
        "renewable_enabled_wh": 0.0,
        "verified_ecological_value": 0.0,
        "energy_embodied_wh": 0.2,
    })


def _mbit() -> MBit:
    return MBit(
        work_id="W1", contributor="test",
        evidence_quality=0.9, reproducibility=1.0,
        utility=0.8, transferability=0.7, human_alignment=0.9,
        evidence_strength=0.85,
    )


class TestMerkle(unittest.TestCase):

    def test_merkle_empty(self):
        self.assertEqual(_merkle([]), "")

    def test_merkle_single(self):
        self.assertEqual(len(_merkle(["a"])), 64)

    def test_merkle_deterministic(self):
        a = _merkle(["x", "y", "z"])
        b = _merkle(["x", "y", "z"])
        self.assertEqual(a, b)


class TestClosureMacro(unittest.TestCase):

    def test_compile_basic(self):
        svca = _svca()
        thermo = _thermo()
        mbit = _mbit()
        compiler = ClosureMacroCompiler()
        bundle = compiler.compile(
            closure_id="MV-CLOSURE-T1",
            parent_closure_id=None,
            scale="MESO",
            title="Test",
            abstract="An abstract",
            svca=svca, thermo=thermo, mbit=mbit,
            repository="MatVerse-py/matverse-organism",
            commit="abc123",
        )
        self.assertEqual(bundle.closure_id, "MV-CLOSURE-T1")
        self.assertEqual(bundle.scale, "MESO")
        self.assertEqual(bundle.state_closure, "CLOSED")
        self.assertEqual(bundle.state_epistemic, "SUPPORTED_FOR_DECLARED_SCOPE")
        self.assertEqual(len(bundle.canonization.merkle_root), 64)
        self.assertEqual(len(bundle.canonical_hash()), 64)

    def test_compile_rejected_mbit(self):
        m = MBit(work_id="W", contributor="x", evidence_quality=0.0)
        compiler = ClosureMacroCompiler()
        bundle = compiler.compile(
            closure_id="MV-CLOSURE-R", parent_closure_id=None,
            scale="MICRO", title="r", abstract="a",
            svca=_svca(), thermo=None, mbit=m,
            repository="x", commit="y",
        )
        self.assertEqual(bundle.state_epistemic, "REFUTED_PRESERVED")

    def test_compile_invalid_scale(self):
        compiler = ClosureMacroCompiler()
        with self.assertRaises(ValueError):
            compiler.compile(
                closure_id="X", parent_closure_id=None,
                scale="NOPE", title="t", abstract="a",
                svca=_svca(), thermo=None, mbit=None,
                repository="x", commit="y",
            )


class TestPublications(unittest.TestCase):

    def _bundle(self):
        svca = _svca()
        thermo = _thermo()
        mbit = _mbit()
        return ClosureMacroCompiler().compile(
            closure_id="MV-CLOSURE-P1", parent_closure_id=None,
            scale="MACRO", title="P", abstract="A",
            svca=svca, thermo=thermo, mbit=mbit,
            repository="MatVerse-py/matverse-organism", commit="c",
        )

    def test_zenodo_metadata(self):
        z = zenodo_metadata(self._bundle(), creators=[{"name": "X"}])
        self.assertEqual(z["status"], "PREPARED_NOT_PUBLISHED")
        self.assertIn("matverse", z["keywords"])

    def test_github_release_metadata(self):
        g = github_release_metadata(self._bundle(),
                                    repo="MatVerse-py/matverse-organism",
                                    tag_name="v3.6.0")
        self.assertEqual(g["status"], "PREPARED_NOT_RELEASED")
        self.assertTrue(g["draft"])

    def test_huggingface_metadata(self):
        h = huggingface_metadata(self._bundle(), repo_id="matverse/x")
        self.assertEqual(h["status"], "PREPARED_NOT_PUBLISHED")
        self.assertIn("card_content", h)

    def test_blockchain_anchor(self):
        b = blockchain_anchor(self._bundle())
        self.assertEqual(b["status"], "PREPARED_NOT_BROADCAST")
        self.assertIn("merkle_root", b["payload"])
        self.assertIn("constitutional_disclaimer", b)

    def test_prepare_publication_aggregates(self):
        b = self._bundle()
        ps = prepare_publication(
            bundle=b,
            creators=[{"name": "X"}],
            github_repo="MatVerse-py/matverse-organism",
            github_tag="v3.6.0",
            hf_repo_id="matverse/test",
        )
        d = ps.to_dict()
        self.assertEqual(d["closure_id"], b.closure_id)
        self.assertEqual(len(d["canonical_hash"]), 64)
        self.assertEqual(d["zenodo"]["status"], "PREPARED_NOT_PUBLISHED")


class TestReplayer(unittest.TestCase):

    def test_replay_matches_for_echo(self):
        umjam = UMJAM()
        r = Replayer(umjam)
        svca = _svca()
        report = r.replay(svca)
        self.assertTrue(report.matches)
        self.assertEqual(report.expected_output_hash, report.output_hash)
        self.assertFalse(report.independent)

    def test_replay_independent_flag(self):
        r = Replayer(UMJAM())
        report = r.replay(_svca(), independent=True)
        self.assertTrue(report.independent)


if __name__ == "__main__":
    unittest.main()
