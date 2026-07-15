"""
Tests for the formal 5-tuple MNB (matverse.mnb_formal).

Covers:
  - The 5-tuple (e, Ψ, C, τ, h)
  - value density ρ = Ψ · τ / C
  - survival under pruning
  - hash verification (tamper detection)
  - MNBState dynamic wrapper
  - ThermodynamicGate (Hamiltonian-based selector)
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from matverse.mnb_formal import (
    FormalMNB, MNBState, MNBPhase, ThermodynamicGate, prune, from_payload,
)


class TestFormalMNB(unittest.TestCase):
    def test_basic_construction(self):
        m = FormalMNB(e="payload", psi=0.8, cost=1.0, tau=1.0)
        self.assertEqual(m.e, "payload")
        self.assertEqual(m.psi, 0.8)
        self.assertEqual(m.cost, 1.0)
        self.assertEqual(m.tau, 1.0)
        self.assertTrue(m.h.startswith("h-"))
        self.assertEqual(len(m.h), len("h-") + 24)

    def test_value_density(self):
        m = FormalMNB(e="x", psi=0.8, cost=2.0, tau=0.5)
        self.assertAlmostEqual(m.value_density(), 0.8 * 0.5 / 2.0)

    def test_survives_pruning_under_threshold(self):
        m = FormalMNB(e="x", psi=0.8, cost=1.0, tau=0.7)
        # ρ = 0.8 · 0.7 / 1.0 = 0.56 > 0.5
        self.assertTrue(m.survives_pruning(0.5))

    def test_dies_under_pruning(self):
        m = FormalMNB(e="x", psi=0.3, cost=1.0, tau=0.3)
        # ρ = 0.09 < 0.5
        self.assertFalse(m.survives_pruning(0.5))

    def test_hash_verifies_clean(self):
        m = FormalMNB(e="x", psi=0.8, cost=1.0, tau=0.7)
        self.assertTrue(m.verify())

    def test_hash_detects_tampering_with_e(self):
        m = FormalMNB(e="x", psi=0.8, cost=1.0, tau=0.7)
        m.e = "tampered"
        self.assertFalse(m.verify())

    def test_invalid_psi_rejected(self):
        with self.assertRaises(ValueError):
            FormalMNB(e="x", psi=1.5, cost=1.0, tau=0.5)

    def test_invalid_cost_rejected(self):
        with self.assertRaises(ValueError):
            FormalMNB(e="x", psi=0.5, cost=0.0, tau=0.5)

    def test_invalid_tau_rejected(self):
        with self.assertRaises(ValueError):
            FormalMNB(e="x", psi=0.5, cost=1.0, tau=-0.1)

    def test_as_tuple(self):
        m = FormalMNB(e="x", psi=0.7, cost=2.0, tau=0.4)
        t = m.as_tuple()
        self.assertEqual(t, ("x", 0.7, 2.0, 0.4, m.h))

    def test_to_dict_includes_rho(self):
        m = FormalMNB(e="x", psi=0.8, cost=1.0, tau=0.5)
        d = m.to_dict()
        self.assertIn("rho", d)
        self.assertAlmostEqual(d["rho"], 0.4)


class TestMNBState(unittest.TestCase):
    def test_state_inherits_mnb(self):
        m = FormalMNB(e="y", psi=0.7, cost=1.0, tau=0.9)
        s = MNBState(id="", mnb=m)
        self.assertTrue(s.id.startswith("MNB-"))
        self.assertEqual(s.phase, MNBPhase.GENESIS)

    def test_adjusted_cost_includes_multiplier(self):
        m = FormalMNB(e="y", psi=0.7, cost=1.0, tau=0.9)
        s = MNBState(id="x", mnb=m, dynamic_cost_multiplier=1.0)
        self.assertAlmostEqual(s.adjusted_cost(), 1.0 * (1.0 + 0.1))

    def test_should_prune_below_threshold(self):
        m = FormalMNB(e="y", psi=0.1, cost=5.0, tau=0.1)
        s = MNBState(id="x", mnb=m)
        self.assertTrue(s.should_prune(rho_min=0.5))

    def test_should_not_prune_above_threshold(self):
        m = FormalMNB(e="y", psi=0.9, cost=1.0, tau=0.9)
        s = MNBState(id="x", mnb=m)
        self.assertFalse(s.should_prune(rho_min=0.5))

    def test_regenerate_reduces_cost(self):
        m = FormalMNB(e="y", psi=0.5, cost=2.0, tau=0.5)
        s = MNBState(id="x", mnb=m)
        original_cost = s.mnb.cost
        s.regenerate()
        self.assertLess(s.mnb.cost, original_cost)
        self.assertEqual(s.phase, MNBPhase.REGENERATED)


class TestThermodynamicGate(unittest.TestCase):
    def test_select_returns_lowest_hamiltonian(self):
        gate = ThermodynamicGate()
        u1 = MNBState(id="a", mnb=FormalMNB(e="a", psi=0.9, cost=1.0, tau=0.9))
        u2 = MNBState(id="b", mnb=FormalMNB(e="b", psi=0.5, cost=5.0, tau=0.5))
        u3 = MNBState(id="c", mnb=FormalMNB(e="c", psi=0.7, cost=2.0, tau=0.7))
        chosen = gate.select([u1, u2, u3], system_load=0.3)
        self.assertIsNotNone(chosen)
        # u1 has highest psi and lowest cost, so should be chosen
        self.assertEqual(chosen.id, "a")

    def test_select_returns_none_if_no_admissible(self):
        gate = ThermodynamicGate()
        u = MNBState(id="x", mnb=FormalMNB(e="x", psi=0.1, cost=10.0, tau=0.1))
        self.assertIsNone(gate.select([u]))

    def test_should_activate_under_high_load(self):
        gate = ThermodynamicGate()
        # Low psi, low tau — should NOT activate under load
        u = MNBState(id="x", mnb=FormalMNB(e="x", psi=0.3, cost=1.0, tau=0.3))
        self.assertFalse(gate.should_activate(u, system_load=0.9))

    def test_force_activate_critical(self):
        gate = ThermodynamicGate()
        # High psi, high tau — force-activate even under load
        u = MNBState(id="x", mnb=FormalMNB(e="x", psi=0.95, cost=1.0, tau=0.95))
        self.assertTrue(gate.force_activate_if_critical(u, system_load=0.99))

    def test_select_all_sorted(self):
        gate = ThermodynamicGate(rho_min=0.05)  # accept lower-density units
        units = [
            MNBState(id=f"u{i}", mnb=FormalMNB(e=f"e{i}", psi=0.5 + i*0.1,
                                                cost=2.0 - i*0.1, tau=0.7))
            for i in range(3)
        ]
        sorted_units = gate.select_all(units)
        self.assertEqual(len(sorted_units), 3)
        # First should have lowest Hamiltonian
        h0 = gate.hamiltonian(sorted_units[0])
        h1 = gate.hamiltonian(sorted_units[1])
        self.assertLessEqual(h0, h1)


class TestPrune(unittest.TestCase):
    def test_prune_splits_survivors_and_pruned(self):
        good = MNBState(id="g", mnb=FormalMNB(e="g", psi=0.9, cost=1.0, tau=0.9))
        bad = MNBState(id="b", mnb=FormalMNB(e="b", psi=0.1, cost=1.0, tau=0.1))
        survivors, pruned = prune([good, bad], rho_min=0.5)
        self.assertEqual(len(survivors), 1)
        self.assertEqual(len(pruned), 1)
        self.assertEqual(survivors[0].id, "g")
        self.assertEqual(pruned[0].id, "b")
        self.assertEqual(pruned[0].phase, MNBPhase.PRUNED)


class TestFromPayload(unittest.TestCase):
    def test_construction_from_payload(self):
        s = from_payload({"k": "v"}, psi=0.85, cost=2.0, tau=0.75)
        self.assertEqual(s.mnb.e, {"k": "v"})
        self.assertEqual(s.mnb.psi, 0.85)
        self.assertEqual(s.mnb.cost, 2.0)
        self.assertEqual(s.mnb.tau, 0.75)
        # value density: 0.85*0.75/2.0 = 0.31875
        self.assertAlmostEqual(s.mnb.value_density(), 0.31875, places=5)


if __name__ == "__main__":
    unittest.main()
