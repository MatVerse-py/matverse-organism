"""Tests for the v3.7 Capability Registry."""
import unittest
import os
import tempfile
from matverse.capability import CapabilityRegistry, CapabilityContract


def _echo_fn(state, inputs):
    return {"echo": state}


class TestCapabilityRegistry(unittest.TestCase):

    def test_register_and_get(self):
        r = CapabilityRegistry()
        c = CapabilityContract(
            id="echo.v1", name="Echo", version="1.0.0",
            implementation=_echo_fn, status="ACTIVE",
        )
        r.register(c)
        self.assertTrue(r.has("echo.v1"))
        self.assertIsNotNone(r.get("echo.v1"))

    def test_register_duplicate_rejected(self):
        r = CapabilityRegistry()
        c = CapabilityContract(id="x.v1", name="x", version="1", implementation=_echo_fn)
        r.register(c)
        with self.assertRaises(ValueError):
            r.register(c)

    def test_supersede(self):
        r = CapabilityRegistry()
        c1 = CapabilityContract(id="x.v1", name="x", version="1",
                                implementation=_echo_fn)
        r.register(c1)
        c2 = CapabilityContract(id="x.v2", name="x", version="2",
                                implementation=_echo_fn)
        r.supersede("x.v1", c2)
        self.assertEqual(r.get_any("x.v1").status, "DEPRECATED")
        self.assertTrue(r.has("x.v2"))
        self.assertIn("x.v1", r.get_any("x.v2").lineage)

    def test_revoke(self):
        r = CapabilityRegistry()
        c = CapabilityContract(id="x.v1", name="x", version="1", implementation=_echo_fn)
        r.register(c)
        r.revoke("x.v1", reason="test")
        self.assertEqual(r.get_any("x.v1").status, "REVOKED")
        self.assertFalse(r.has("x.v1"))

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "caps.json")
            r1 = CapabilityRegistry(disk_path=path)
            r1.register(CapabilityContract(
                id="x.v1", name="x", version="1", implementation=_echo_fn,
            ))
            r2 = CapabilityRegistry(disk_path=path)
            r2.load()
            self.assertIsNotNone(r2.get("x.v1"))

    def test_register_builtins(self):
        r = CapabilityRegistry()
        r.register_builtins()
        ids = [c.id for c in r.list("ACTIVE")]
        self.assertIn("echo.v1", ids)
        self.assertIn("paired_metric_comparison.v1", ids)
        self.assertIn("monte_carlo_propagation.v1", ids)
        self.assertIn("ast_diff.v1", ids)
        self.assertIn("hypothesis_decompose.v1", ids)
        # At least 10 builtins
        self.assertGreaterEqual(len(ids), 10)

    def test_select_for(self):
        r = CapabilityRegistry()
        r.register_builtins()
        # All builtins are LOW risk
        lows = r.select_for({"risk_level": "LOW"})
        self.assertGreater(len(lows), 0)
        # No MEDIUM-risk builtins in the default set
        meds = r.select_for({"risk_level": "MEDIUM"})
        self.assertEqual(len(meds), 0)

    def test_validate(self):
        from matverse.adaptation import AutopoiesisGenerator, CapabilityGap
        r = CapabilityRegistry()
        gen = AutopoiesisGenerator(r)
        c = gen.propose(CapabilityGap(
            name="Test Cap", inputs={"x": "number"},
            outputs={"y": "number"},
        ))
        issues = gen.validate(c)
        self.assertIn("missing implementation", issues)
        ok, issues = gen.register_if_valid(c)
        self.assertFalse(ok)

        # Provide an implementation
        c2 = gen.propose(CapabilityGap(
            name="Test Cap 2", inputs={"x": "number"},
            outputs={"y": "number"},
        ))
        # Manually set the implementation
        c2.implementation = _echo_fn
        ok, issues = gen.register_if_valid(c2)
        self.assertTrue(ok, msg=issues)


if __name__ == "__main__":
    unittest.main()
