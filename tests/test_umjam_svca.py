"""Tests for UMJAM (transmutation) and SVCA (proof capsule)."""
import unittest
from matverse.umjam import UMJAM, UMJAMSpec, CapabilityRegistry
from matverse.svca import SVCA


def _paired_state() -> dict:
    return {"baseline": [1, 2, 3, 4, 5], "candidate": [1.5, 2.5, 3.5, 4.5, 5.5]}


class TestUMJAM(unittest.TestCase):

    def test_paired_metric_comparison(self):
        umjam = UMJAM()
        spec = UMJAMSpec(
            operation_id="OP1", capability_id="paired_metric_comparison.v1",
            inputs=_paired_state(), seed=42, purpose="test",
        )
        r = umjam.transmute(spec, _paired_state())
        self.assertEqual(r.status, "PASS")
        self.assertIn("mean", r.output)
        self.assertEqual(r.output["n"], 5)
        self.assertGreater(r.output["mean"], 0)

    def test_echo_capability(self):
        umjam = UMJAM()
        spec = UMJAMSpec(operation_id="OP2", capability_id="echo.v1",
                         inputs={"x": 1}, seed=0)
        r = umjam.transmute(spec, {"x": 1})
        self.assertEqual(r.status, "PASS")
        self.assertEqual(r.output, {"echo": {"x": 1}})

    def test_unknown_capability_refused(self):
        umjam = UMJAM()
        spec = UMJAMSpec(operation_id="OP3", capability_id="missing.v1",
                         inputs={}, seed=0)
        r = umjam.transmute(spec, {})
        self.assertEqual(r.status, "REFUSED")
        self.assertIn("unknown capability", r.refusal_reason)

    def test_state_must_be_dict(self):
        umjam = UMJAM()
        spec = UMJAMSpec(operation_id="OP4", capability_id="echo.v1",
                         inputs={}, seed=0)
        r = umjam.transmute(spec, "not a dict")
        self.assertEqual(r.status, "REFUSED")

    def test_capability_raising_yields_refused(self):
        reg = CapabilityRegistry()
        def broken(state, spec):
            raise RuntimeError("nope")
        reg.register("broken.v1", broken)
        umjam = UMJAM(registry=reg)
        spec = UMJAMSpec(operation_id="OP5", capability_id="broken.v1",
                         inputs={}, seed=0)
        r = umjam.transmute(spec, {})
        self.assertEqual(r.status, "REFUSED")
        self.assertIn("capability raised", r.refusal_reason)

    def test_nan_rejected(self):
        reg = CapabilityRegistry()
        def bad(state, spec):
            return {"v": float("nan")}
        reg.register("nan.v1", bad)
        umjam = UMJAM(registry=reg)
        spec = UMJAMSpec(operation_id="OP6", capability_id="nan.v1",
                         inputs={}, seed=0)
        r = umjam.transmute(spec, {})
        self.assertEqual(r.status, "REFUSED")
        self.assertIn("non-finite", r.refusal_reason)


class TestSVCA(unittest.TestCase):

    def test_svca_from_transmutation(self):
        umjam = UMJAM()
        spec = UMJAMSpec(
            operation_id="OP_SVCA",
            capability_id="paired_metric_comparison.v1",
            inputs=_paired_state(), seed=42,
        )
        r = umjam.transmute(spec, _paired_state())
        svca = SVCA.from_transmutation(spec, r, metrics={"x": 1})
        self.assertEqual(svca.capability_id, "paired_metric_comparison.v1")
        self.assertEqual(svca.status, "PASS")
        self.assertIn("input_hash", svca.hashes)
        self.assertIn("output_hash", svca.hashes)
        self.assertIn("receipt_hash", svca.hashes)
        self.assertTrue(svca.is_reproducible())

    def test_svca_canonical_hash_stable(self):
        umjam = UMJAM()
        spec = UMJAMSpec(operation_id="OP_HASH", capability_id="echo.v1",
                         inputs={"a": 1}, seed=0)
        r = umjam.transmute(spec, {"a": 1})
        svca = SVCA.from_transmutation(spec, r)
        h1 = svca.canonical_hash()
        h2 = svca.canonical_hash()
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)


if __name__ == "__main__":
    unittest.main()
