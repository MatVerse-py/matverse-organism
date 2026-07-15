"""
Tests for the 12-organism constitutional taxonomy (matverse.canonical).

Covers:
  - 12 constitutional organs (v3.8.0)
  - 3 constitutional-physics objects
  - Cycle order
  - Constitutional completeness check
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from matverse.canonical import (
    CONSTITUTIONAL_ORGANS_V3_8, CONSTITUTIONAL_PHYSICS_V3_8,
    ConstitutionalState, next_organ,
)


class TestConstitutionalOrgans(unittest.TestCase):
    def test_twelve_organs(self):
        self.assertEqual(len(CONSTITUTIONAL_ORGANS_V3_8), 12)

    def test_mmnb_first_and_atlas_present(self):
        self.assertEqual(CONSTITUTIONAL_ORGANS_V3_8[0], "MMNB")
        self.assertIn("ATLAS", CONSTITUTIONAL_ORGANS_V3_8)
        self.assertIn("THERMO_CORTEX", CONSTITUTIONAL_ORGANS_V3_8)
        self.assertIn("CAPTALS", CONSTITUTIONAL_ORGANS_V3_8)
        self.assertIn("EXISTENTIAL", CONSTITUTIONAL_ORGANS_V3_8)

    def test_all_organs_unique(self):
        self.assertEqual(len(CONSTITUTIONAL_ORGANS_V3_8),
                         len(set(CONSTITUTIONAL_ORGANS_V3_8)))


class TestConstitutionalPhysics(unittest.TestCase):
    def test_three_physics(self):
        self.assertEqual(len(CONSTITUTIONAL_PHYSICS_V3_8), 3)
        self.assertIn("GTHDL_HAMILTONIAN", CONSTITUTIONAL_PHYSICS_V3_8)
        self.assertIn("RIEMANNIAN_MANIFOLD", CONSTITUTIONAL_PHYSICS_V3_8)
        self.assertIn("EPISTEMIC_STATE", CONSTITUTIONAL_PHYSICS_V3_8)


class TestNextOrgan(unittest.TestCase):
    def test_next_in_cycle(self):
        self.assertEqual(next_organ("MMNB"), "CASSANDRA_METACORTEX")
        self.assertEqual(next_organ("COG"), "INVARIANTS")
        self.assertEqual(next_organ("EXISTENTIAL"), None)

    def test_unknown_returns_none(self):
        self.assertIsNone(next_organ("UNKNOWN"))


class TestConstitutionalState(unittest.TestCase):
    def test_default_state_is_complete(self):
        s = ConstitutionalState(omega=0.9)
        self.assertTrue(s.is_constitutionally_complete())

    def test_low_omega_is_incomplete(self):
        s = ConstitutionalState(omega=0.3)
        self.assertFalse(s.is_constitutionally_complete())

    def test_missing_organ_is_incomplete(self):
        s = ConstitutionalState(omega=0.9,
                                 organs_present=CONSTITUTIONAL_ORGANS_V3_8[:10])
        self.assertFalse(s.is_constitutionally_complete())

    def test_to_dict(self):
        s = ConstitutionalState(omega=0.85, cycle_position=5)
        d = s.to_dict()
        self.assertEqual(d["n_organs"], 12)
        self.assertEqual(d["n_physics"], 3)
        self.assertEqual(d["omega"], 0.85)
        self.assertEqual(d["cycle_position"], 5)
        self.assertTrue(d["constitutionally_complete"])


if __name__ == "__main__":
    unittest.main()
