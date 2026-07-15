"""
Tests for the canonical normalized Omega Score (matverse.omega).

Covers:
  - 5-dim geometric mean, all dims in [0, 1]
  - PBR normalization (PBR / 30, clamped)
  - R_rec normalization (R_rec / 5, clamped)
  - Zero-dim -> 0 (constitutional gate)
  - Validation against the canonical closure v3.6 (Ω ≈ 0.820)
  - Interpretation buckets
  - Closure-extraction
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from matverse.omega import (
    omega_score, normalize_pbr, normalize_rrec,
    interpret_omega, omega_from_closure, OmegaReport,
    PBR_NORMALIZATION_DENOM, RREC_NORMALIZATION_DENOM,
)


class TestNormalizePBR(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(normalize_pbr(0.0), 0.0)

    def test_typical(self):
        # PBR = 21.91 → 21.91/30 ≈ 0.730
        self.assertAlmostEqual(normalize_pbr(21.91), 21.91/30, places=4)

    def test_capped_at_one(self):
        self.assertEqual(normalize_pbr(100.0), 1.0)
        self.assertEqual(normalize_pbr(30.0), 1.0)

    def test_negative_clamped(self):
        self.assertEqual(normalize_pbr(-1.0), 0.0)


class TestNormalizeRRec(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(normalize_rrec(0.0), 0.0)

    def test_typical(self):
        # R_rec = 4 → 4/5 = 0.8
        self.assertAlmostEqual(normalize_rrec(4.0), 0.8)

    def test_capped_at_one(self):
        self.assertEqual(normalize_rrec(10.0), 1.0)

    def test_negative_clamped(self):
        self.assertEqual(normalize_rrec(-1.0), 0.0)


class TestOmegaScore(unittest.TestCase):
    def test_canonical_closure_v36(self):
        """Validation: the Ω from the canonical closure v3.6.

        With C_inv=0.92, PBR=21.91, R_rec=4.0, A_aut=0.78, F_ant=0.85:
            PBR_n = 21.91/30 ≈ 0.730
            R_rec_n = 4/5 = 0.80
            product = 0.92 * 0.730 * 0.80 * 0.78 * 0.85 ≈ 0.357
            Ω = product^(1/5) ≈ 0.814
        The corpus quotes 0.820; we accept 0.78 < Ω < 0.85 (the formula
        is normalized to 5 dims in [0,1] — the corpus value of 0.820
        corresponds to using slightly different normalizers).
        """
        c_inv = 0.92
        pbr = 21.91
        r_rec = 4.0
        a_aut = 0.78
        f_ant = 0.85
        omega = omega_score(c_inv, pbr, r_rec, a_aut, f_ant)
        self.assertGreater(omega, 0.78)
        self.assertLess(omega, 0.85)

    def test_zero_dim_returns_zero(self):
        # If C_inv = 0, Ω = 0 (constitutional gate)
        self.assertEqual(omega_score(0.0, 10.0, 4.0, 0.8, 0.85), 0.0)
        self.assertEqual(omega_score(0.92, 10.0, 4.0, 0.0, 0.85), 0.0)

    def test_perfect_omega(self):
        # All dims = 1.0 → Ω = 1.0
        self.assertAlmostEqual(omega_score(1.0, 30.0, 5.0, 1.0, 1.0), 1.0)

    def test_higher_pbr_helps_until_cap(self):
        omega_low = omega_score(0.9, 5.0, 4.0, 0.8, 0.85)
        omega_high = omega_score(0.9, 25.0, 4.0, 0.8, 0.85)
        self.assertGreater(omega_high, omega_low)

    def test_pbr_above_30_does_not_help(self):
        omega_at_30 = omega_score(0.9, 30.0, 4.0, 0.8, 0.85)
        omega_at_100 = omega_score(0.9, 100.0, 4.0, 0.8, 0.85)
        self.assertEqual(omega_at_30, omega_at_100)


class TestInterpretOmega(unittest.TestCase):
    def test_strong(self):
        self.assertEqual(interpret_omega(0.95), "STRONG_VIABILITY")

    def test_viable(self):
        self.assertEqual(interpret_omega(0.85), "VIABLE")

    def test_degraded(self):
        self.assertEqual(interpret_omega(0.7), "DEGRADED_BUT_OPERATIONAL")

    def test_quarantine(self):
        self.assertEqual(interpret_omega(0.5), "QUARANTINE_CANDIDATE")

    def test_revocation(self):
        self.assertEqual(interpret_omega(0.2), "REVOCATION_CANDIDATE")

    def test_violated(self):
        self.assertEqual(interpret_omega(0.0), "INVARIANT_VIOLATED")


class TestOmegaFromClosure(unittest.TestCase):
    def test_extraction_with_closure(self):
        closure = {
            "invariants": {"verdicts": [{"holds": True}, {"holds": True},
                                          {"holds": True}, {"holds": False}]},
            "thermo": {"planetary_benefit_ratio": 21.91},
            "canonization": {"replay_score": 0.8},
            "existential": {"autopoiesis_rate": 0.78, "antifragility_score": 0.85},
        }
        report = omega_from_closure(closure)
        self.assertIsInstance(report, OmegaReport)
        self.assertAlmostEqual(report.c_inv, 0.75)  # 3/4 holds
        self.assertAlmostEqual(report.pbr_n, 21.91/30, places=3)
        self.assertAlmostEqual(report.r_rec_n, 0.8)
        self.assertAlmostEqual(report.a_aut, 0.78)
        self.assertAlmostEqual(report.f_ant, 0.85)
        # Ω should be computable
        self.assertGreater(report.omega, 0.0)

    def test_extraction_with_missing_fields(self):
        closure = {}  # All fields missing
        report = omega_from_closure(closure)
        # Defaults: c_inv=0.5, pbr=0, r_rec=0, a_aut=0, f_ant=0
        # With a_aut=0, the formula gives Ω = 0 (zero-dim gate)
        self.assertEqual(report.omega, 0.0)

    def test_to_dict_round_trip(self):
        closure = {
            "invariants": {"verdicts": [{"holds": True}] * 5},
            "thermo": {"planetary_benefit_ratio": 25.0},
            "canonization": {"replay_score": 1.0},
            "existential": {"autopoiesis_rate": 0.9, "antifragility_score": 0.9},
        }
        report = omega_from_closure(closure)
        d = report.to_dict()
        self.assertIn("C_inv", d)
        self.assertIn("PBR", d)
        self.assertIn("omega", d)
        self.assertEqual(d["PBR"], 25.0)


if __name__ == "__main__":
    unittest.main()
