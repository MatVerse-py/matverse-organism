"""Tests for ThermoCortex, Captals engine, and proof chain."""
import unittest
from matverse.thermo import (
    ThermoCortex, exergy, planetary_benefit_ratio, DeclaredProbe,
)
from matverse.captals import (
    CaptalsEngine, MBit, ProofChain, WorkContract, LCUAccount,
)


class TestExergy(unittest.TestCase):

    def test_exergy_at_ambient_is_zero(self):
        # When source temp == ambient, no useful work
        self.assertAlmostEqual(exergy(100.0, 20.0, ambient_temp_c=20.0), 0.0, places=3)

    def test_exergy_grows_with_temperature(self):
        e1 = exergy(100.0, 100.0, ambient_temp_c=20.0)
        e2 = exergy(100.0, 500.0, ambient_temp_c=20.0)
        self.assertGreater(e2, e1)


class TestPBR(unittest.TestCase):

    def test_pbr_net_consumer(self):
        p = planetary_benefit_ratio(1, 0, 0, 0, 10, 0)
        self.assertLess(p, 1.0)

    def test_pbr_regenerative_candidate(self):
        p = planetary_benefit_ratio(10, 5, 0, 0, 1, 1)
        self.assertGreater(p, 1.0)

    def test_pbr_zero_when_no_energy(self):
        self.assertEqual(planetary_benefit_ratio(0, 0, 0, 0, 0, 0), 0.0)


class TestThermoCortex(unittest.TestCase):

    def test_record_produces_receipt(self):
        tc = ThermoCortex()
        r = tc.record("EX1", {
            "energy_wh": 1.0, "co2_g": 0.1, "exergy_wh": 0.8,
            "cpu_seconds": 0.5, "input_tokens": 100,
            "output_tokens": 50, "avg_power_w": 5.0,
            "external_energy_avoided_wh": 5.0,
            "heat_recovered_wh": 0.1,
            "renewable_enabled_wh": 0.0,
            "verified_ecological_value": 0.0,
            "energy_embodied_wh": 0.2,
        })
        self.assertEqual(r.execution_id, "EX1")
        self.assertGreater(r.regenerative_ratio, 0.0)
        self.assertGreater(r.planetary_benefit_ratio, 0.0)

    def test_declared_probe_returns_declared_status(self):
        tc = ThermoCortex()
        r = tc.record("EX2", {"energy_wh": 0.5, "co2_g": 0.05,
                              "external_energy_avoided_wh": 0.0})
        self.assertEqual(r.measurement_status, "DECLARED")

    def test_aggregate(self):
        tc = ThermoCortex()
        tc.record("EX1", {"energy_wh": 1.0, "co2_g": 0.1,
                          "external_energy_avoided_wh": 5.0})
        tc.record("EX2", {"energy_wh": 2.0, "co2_g": 0.2,
                          "external_energy_avoided_wh": 8.0})
        a = tc.aggregate()
        self.assertEqual(a["n"], 2)
        self.assertGreater(a["total_energy_wh"], 0.0)


class TestMBit(unittest.TestCase):

    def test_zero_dimension_means_zero_score(self):
        m = MBit(work_id="W1", contributor="x",
                 compute_cost=0.5, evidence_quality=0.0,  # zero
                 reproducibility=1.0, utility=0.8,
                 transferability=0.7, risk=0.0, human_alignment=0.95)
        self.assertEqual(m.geometric_score(), 0.0)

    def test_full_dimensions_have_positive_score(self):
        m = MBit(work_id="W2", contributor="x",
                 compute_cost=0.5, evidence_quality=0.9,
                 reproducibility=1.0, utility=0.8,
                 transferability=0.7, risk=0.0, human_alignment=0.95,
                 evidence_strength=0.9)
        self.assertGreater(m.geometric_score(), 0.0)


class TestProofChain(unittest.TestCase):

    def test_attach_and_complete(self):
        pc = ProofChain()
        pc.attach("W1", "PoSE", "a" * 64)
        pc.attach("W1", "PoCT", "b" * 64)
        self.assertFalse(pc.is_complete("W1"))
        pc.attach("W1", "PoTM", "c" * 64)
        pc.attach("W1", "PoLE", "d" * 64)
        self.assertTrue(pc.is_complete("W1"))

    def test_unknown_kind_rejected(self):
        pc = ProofChain()
        with self.assertRaises(ValueError):
            pc.attach("W1", "BAD", "x")


class TestCaptalsEngine(unittest.TestCase):

    def test_record_rejected_mbit(self):
        e = CaptalsEngine()
        m = MBit(work_id="W", contributor="x", evidence_quality=0.0)
        e.record(m)
        self.assertEqual(m.status, "REJECTED")
        self.assertEqual(e.summary()["n_rejected"], 1)

    def test_record_admissible(self):
        e = CaptalsEngine()
        m = MBit(work_id="W", contributor="x",
                 evidence_quality=0.9, reproducibility=1.0,
                 utility=0.8, transferability=0.7, human_alignment=0.9,
                 evidence_strength=0.85)
        e.record(m)
        self.assertEqual(m.status, "ADMISSIBLE_CONTRIBUTION")

    def test_reward_distribution(self):
        e = CaptalsEngine()
        m1 = MBit(work_id="W1", contributor="x", evidence_quality=0.9,
                  reproducibility=1.0, utility=0.9, transferability=0.9,
                  human_alignment=0.9, evidence_strength=0.9)
        m2 = MBit(work_id="W2", contributor="x", evidence_quality=0.5,
                  reproducibility=0.5, utility=0.5, transferability=0.5,
                  human_alignment=0.5, evidence_strength=0.5)
        e.record(m1); e.record(m2)
        rewards = e.reward(1000.0,
                           difficulty={"W1": 1.0, "W2": 1.0},
                           admissibility={"W1": 1.0, "W2": 1.0},
                           participation={"W1": 1.0, "W2": 1.0})
        self.assertGreater(rewards["W1"], rewards["W2"])
        # Total should equal budget (up to float precision)
        self.assertAlmostEqual(sum(rewards.values()), 1000.0, places=2)


class TestLCU(unittest.TestCase):

    def test_total(self):
        lcu = LCUAccount(in_tokens=100, out_tokens=50,
                        cpu_seconds=1.0, gpu_seconds=0.0, energy_wh=0.5)
        self.assertGreater(lcu.total(), 100.0 + 50.0 * 3.0)  # kappa default

    def test_add(self):
        a = LCUAccount(in_tokens=10)
        b = LCUAccount(in_tokens=20)
        a.add(b)
        self.assertEqual(a.in_tokens, 30)


class TestWorkContract(unittest.TestCase):

    def test_to_dict(self):
        c = WorkContract(
            work_id="W1", dao_id="DAO", problem_hash="h",
            closure_target="x", accepted_capabilities=["echo.v1"],
            evaluation={"tests_required": 10},
            compute_budget={"max_cpu_seconds": 60},
            risk={"network": "DENIED"},
            reward_pool_captals_units=100.0,
            challenge_window_seconds=86400,
        )
        d = c.to_dict()
        self.assertEqual(d["work_id"], "W1")
        self.assertEqual(d["state"], "OPEN")


if __name__ == "__main__":
    unittest.main()
