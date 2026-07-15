"""Tests for the MMNB seed module."""
import unittest
from matverse.seeds import SEED_V3_2026_07_14, fingerprint


class TestSeeds(unittest.TestCase):

    def test_seed_has_required_fields(self):
        for k in ("id", "name", "epoch", "initial_cells",
                  "initial_capabilities", "axioms", "phi_constant"):
            self.assertIn(k, SEED_V3_2026_07_14)

    def test_fingerprint_deterministic(self):
        a = fingerprint(SEED_V3_2026_07_14)
        b = fingerprint(SEED_V3_2026_07_14)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 64)


if __name__ == "__main__":
    unittest.main()
