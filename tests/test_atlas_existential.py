"""Tests for Atlas and the existential organs."""
import unittest
from matverse.atlas import Atlas, AtlasNode, AtlasEdge
from matverse.existential import (
    Metabolism, MetabolismBudget, Autopoiesis, Apoptosis,
    Antifragility, Homeostasis, APOPTOSIS_STATES,
)


class TestAtlas(unittest.TestCase):

    def test_register_organ(self):
        a = Atlas()
        a.register_organ("organ.x", "X")
        n = a.nodes("organ")
        self.assertEqual(len(n), 1)
        self.assertEqual(n[0].state, "ACTIVE")

    def test_register_capability_creates_edge(self):
        a = Atlas()
        a.register_organ("organ.umjam", "UMJAM")
        a.register_capability("echo.v1", "organ.umjam")
        es = a.edges()
        self.assertTrue(any(e.relation == "registered_in" for e in es))

    def test_record_svca_creates_edges(self):
        a = Atlas()
        a.register_organ("organ.umjam", "UMJAM")
        a.register_capability("echo.v1", "organ.umjam")
        a.record_svca("S1", "echo.v1", "P1")
        es = a.edges()
        self.assertTrue(any(e.relation == "produced_by" for e in es))
        self.assertTrue(any(e.relation == "evidence_for" for e in es))

    def test_record_closure_with_parent(self):
        a = Atlas()
        a.record_closure("C1", parent_closure_id=None, svca_ids=["S1"])
        a.record_closure("C2", parent_closure_id="C1", svca_ids=["S1"])
        es = a.edges()
        self.assertTrue(any(e.src == "C2" and e.dst == "C1" for e in es))

    def test_health_summary(self):
        a = Atlas()
        a.register_organ("a", "A", state="ACTIVE")
        a.register_organ("b", "B", state="QUARANTINED")
        h = a.health()
        self.assertEqual(h["total_nodes"], 2)
        self.assertEqual(h["states"].get("ACTIVE"), 1)
        self.assertEqual(h["states"].get("QUARANTINED"), 1)


class TestMetabolism(unittest.TestCase):

    def test_viability_geometric_mean(self):
        m = Metabolism(MetabolismBudget(vital=10, service=20,
                                        learning=30, regeneration=40))
        v = m.budget.viability()
        # all 4 fractions are 1.0, so the geometric mean is 1.0
        self.assertAlmostEqual(v, 1.0, places=3)

    def test_spend_reduces_viability(self):
        m = Metabolism(MetabolismBudget(vital=10, service=20,
                                        learning=30, regeneration=40))
        self.assertTrue(m.spend("service", 5.0))
        self.assertLess(m.budget.viability(), 1.0)

    def test_cannot_spend_past_reserve(self):
        m = Metabolism(MetabolismBudget(vital=10, service=20,
                                        learning=30, regeneration=40))
        self.assertFalse(m.spend("service", 1000.0))


class TestApoptosis(unittest.TestCase):

    def test_state_progression(self):
        a = Apoptosis()
        a.register("cap.x")
        a.transition("cap.x", "DEGRADED", reason="tests fail")
        a.transition("cap.x", "QUARANTINED", reason="low quality")
        a.transition("cap.x", "REVOKED", reason="unsafe")
        c = a.cases["cap.x"]
        self.assertEqual(c.current_state, "REVOKED")
        self.assertEqual(len(c.history), 3)

    def test_revoked_requires_prior_quarantine(self):
        a = Apoptosis()
        a.register("cap.y")
        with self.assertRaises(ValueError):
            a.transition("cap.y", "REVOKED", reason="x")

    def test_is_alive_only_for_active(self):
        a = Apoptosis()
        a.register("z")
        self.assertTrue(a.is_alive("z"))
        a.transition("z", "DEGRADED", reason="x")
        self.assertFalse(a.is_alive("z"))


class TestAntifragility(unittest.TestCase):

    def test_score_with_insufficient_samples_is_zero(self):
        a = Antifragility(min_samples=3)
        a.record("p", 0.0, 1.0)
        self.assertEqual(a.score(), 0.0)

    def test_positive_score_with_enough_samples(self):
        a = Antifragility(min_samples=3)
        a.record("p1", 0.0, 1.0)
        a.record("p2", 0.0, 0.5)
        a.record("p3", 0.0, 2.0)
        self.assertGreater(a.score(), 0.0)
        self.assertTrue(a.is_antifragile())


class TestHomeostasis(unittest.TestCase):

    def test_in_region(self):
        h = Homeostasis()
        h.register_region("temp", 0, 100)
        self.assertTrue(h.in_region("temp", 50))
        self.assertFalse(h.in_region("temp", 150))

    def test_deviation(self):
        h = Homeostasis()
        h.register_region("temp", 0, 100)
        self.assertEqual(h.deviation("temp", 50), 0.0)
        self.assertEqual(h.deviation("temp", 110), 10.0)
        self.assertEqual(h.deviation("temp", -5), 5.0)


if __name__ == "__main__":
    unittest.main()
