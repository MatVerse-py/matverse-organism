"""
Tests for the Riemannian Memory Manifold (matverse.riemannian).

Covers:
  - Metric tensor g (symmetric, trace-normalized)
  - Curvature tensor R (sparse)
  - Geodesic distances
  - Information flow Φ (metric update)
  - Probability distribution ρ over units
  - Manifold health
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from matverse.mnb_formal import FormalMNB, MNBState
from matverse.riemannian import (
    MetricTensor, CurvatureTensor, RiemannianMemoryManifold,
    adjusted_cost_manifold, _feature_vector,
)


class TestMetricTensor(unittest.TestCase):
    def test_identity_ish_initialization(self):
        g = MetricTensor(dim=4, seed=42)
        for i in range(4):
            for j in range(4):
                if i == j:
                    self.assertGreater(g.get(i, j), 0.5)
                else:
                    # Off-diagonal should be small (small perturbation)
                    self.assertLess(abs(g.get(i, j)), 0.1)

    def test_symmetry(self):
        g = MetricTensor(dim=4, seed=42)
        for i in range(4):
            for j in range(4):
                self.assertAlmostEqual(g.get(i, j), g.get(j, i))

    def test_geodesic_distance_to_self_zero(self):
        g = MetricTensor(dim=4, seed=42)
        a = [0.5, 0.3, 0.7, 0.1]
        self.assertAlmostEqual(g.geodesic_distance(a, a), 0.0, places=6)

    def test_geodesic_distance_symmetric(self):
        g = MetricTensor(dim=4, seed=42)
        a = [0.1, 0.2, 0.3, 0.4]
        b = [0.4, 0.3, 0.2, 0.1]
        d_ab = g.geodesic_distance(a, b)
        d_ba = g.geodesic_distance(b, a)
        self.assertAlmostEqual(d_ab, d_ba, places=6)

    def test_update_preserves_symmetry(self):
        g = MetricTensor(dim=4, seed=42)
        feedback = [0.1, 0.2, 0.3, 0.4]
        g.update(feedback, lr=0.01)
        for i in range(4):
            for j in range(4):
                self.assertAlmostEqual(g.get(i, j), g.get(j, i))

    def test_update_wrong_dim_raises(self):
        g = MetricTensor(dim=4, seed=42)
        with self.assertRaises(ValueError):
            g.update([0.1, 0.2], lr=0.01)

    def test_frobenius_norm_positive(self):
        g = MetricTensor(dim=4, seed=42)
        self.assertGreater(g.frobenius_norm(), 0.0)


class TestCurvatureTensor(unittest.TestCase):
    def test_initialization_creates_sparse_entries(self):
        R = CurvatureTensor(dim=4, seed=42)
        # Should have some entries
        self.assertGreater(len(R.entries), 0)

    def test_local_curvature_norm_positive(self):
        R = CurvatureTensor(dim=4, seed=42)
        norm = R.local_curvature_norm([0.0, 0.0, 0.0, 0.0])
        self.assertGreater(norm, 0.0)

    def test_evolve_does_not_explode(self):
        R = CurvatureTensor(dim=4, seed=42)
        initial_n = len(R.entries)
        R.evolve([0.1] * 4, lr=0.01)
        # Should still have entries
        self.assertGreater(len(R.entries), 0)
        # And not have an absurd number
        self.assertLess(len(R.entries), 10000)


class TestFeatureVector(unittest.TestCase):
    def test_feature_vector_4dim(self):
        u = MNBState(id="x", mnb=FormalMNB(e="x", psi=0.7, cost=1.0, tau=0.5),
                     activation_count=3, dynamic_cost_multiplier=0.0)
        f = _feature_vector(u)
        self.assertEqual(len(f), 4)
        self.assertEqual(f[0], 0.7)   # psi
        self.assertEqual(f[1], 0.5)   # tau
        self.assertEqual(f[2], 0.25)  # 1/(1+3)
        self.assertAlmostEqual(f[3], 1.0)   # 1/cost (with mult=0)

    def test_feature_vector_handles_low_cost_gracefully(self):
        # Use a very low (but valid) cost to verify the max(1e-9, ...) guard
        u = MNBState(id="x", mnb=FormalMNB(e="x", psi=0.5, cost=0.1, tau=0.5),
                     dynamic_cost_multiplier=0.0)
        f = _feature_vector(u)
        self.assertEqual(len(f), 4)
        self.assertGreater(f[3], 0.0)


class TestRiemannianMemoryManifold(unittest.TestCase):
    def setUp(self):
        self.units = [
            MNBState(id="a", mnb=FormalMNB(e="a", psi=0.9, cost=1.0, tau=0.9)),
            MNBState(id="b", mnb=FormalMNB(e="b", psi=0.5, cost=1.0, tau=0.5)),
        ]
        self.m = RiemannianMemoryManifold(units=self.units, seed=42)

    def test_construction(self):
        self.assertEqual(self.m.g.dim, 4)
        self.assertEqual(self.m.g.frobenius_norm() > 0, True)

    def test_geodesic_distance_between_units(self):
        d = self.m.geodesic_distance(self.units[0], self.units[1])
        self.assertGreater(d, 0.0)

    def test_pairwise_distances_shape(self):
        D = self.m.pairwise_distances()
        self.assertEqual(len(D), 2)
        self.assertEqual(len(D[0]), 2)
        # Diagonal is zero
        self.assertAlmostEqual(D[0][0], 0.0)
        self.assertAlmostEqual(D[1][1], 0.0)
        # Symmetric
        self.assertAlmostEqual(D[0][1], D[1][0])

    def test_local_curvature_norm(self):
        n = self.m.local_curvature_norm(self.units[0])
        self.assertGreaterEqual(n, 0.0)

    def test_flow_updates_metric(self):
        g_before = self.m.g.frobenius_norm()
        self.m.flow([0.5, 0.5, 0.5, 0.5], lr=0.01)
        g_after = self.m.g.frobenius_norm()
        # Frobenius norm changes (might go up or down, but must change)
        self.assertNotAlmostEqual(g_before, g_after, places=6)
        # And the feedback is recorded
        self.assertEqual(self.m.flow_history[-1], [0.5, 0.5, 0.5, 0.5])

    def test_flow_wrong_dim_raises(self):
        with self.assertRaises(ValueError):
            self.m.flow([0.1, 0.2], lr=0.01)

    def test_probability_over_units(self):
        p = self.m.probability_over_units()
        self.assertEqual(len(p), 2)
        self.assertAlmostEqual(sum(p), 1.0)
        # u_a has higher ρ than u_b
        self.assertGreater(p[0], p[1])

    def test_manifold_health(self):
        h = self.m.manifold_health()
        self.assertEqual(h["n_units"], 2)
        self.assertEqual(h["g_dim"], 4)
        self.assertIn("R_entries", h)
        self.assertIn("rho_entropy", h)
        self.assertGreaterEqual(h["rho_entropy"], 0.0)

    def test_adjusted_cost_manifold(self):
        cost = adjusted_cost_manifold(self.units[0], self.m)
        # cost = C · (1 + ‖R‖_local), with ‖R‖ ≥ 0
        self.assertGreaterEqual(cost, self.units[0].mnb.cost)


class TestEmptyManifold(unittest.TestCase):
    def test_empty_manifold_construction(self):
        m = RiemannianMemoryManifold(units=[], seed=0)
        # Should still construct without crashing
        self.assertEqual(m.units, [])
        self.assertEqual(m.g.dim, 4)
        self.assertEqual(m.probability_over_units(), [])


if __name__ == "__main__":
    unittest.main()
