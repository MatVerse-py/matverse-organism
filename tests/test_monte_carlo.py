"""Tests for the Monte Carlo module."""
import unittest
import math
from matverse.monte_carlo import (
    monte_carlo, summarize, cvar, threshold_probability, sensitivity, is_finite_number,
)


class TestMonteCarlo(unittest.TestCase):

    def test_monte_carlo_reproducible(self):
        a = monte_carlo(100, lambda: 0.5, seed=42)
        b = monte_carlo(100, lambda: 0.5, seed=42)
        self.assertEqual(a, b)

    def test_monte_carlo_rejects_huge_n(self):
        with self.assertRaises(ValueError):
            monte_carlo(2_000_000, lambda: 0.0, seed=1)

    def test_summarize_empty(self):
        s = summarize([])
        self.assertEqual(s["mean"], 0.0)
        self.assertEqual(s["p50"], 0.0)

    def test_summarize_basic(self):
        vals = list(range(1, 101))
        s = summarize(vals)
        self.assertAlmostEqual(s["mean"], 50.5, places=1)
        self.assertAlmostEqual(s["min"], 1.0)
        self.assertAlmostEqual(s["max"], 100.0)

    def test_cvar_tail(self):
        vals = list(range(1, 101))
        # bottom 10% mean should be roughly (1+2+...+10)/10 = 5.5
        self.assertAlmostEqual(cvar(vals, alpha=0.10), 5.5, places=1)

    def test_threshold_probability_above(self):
        vals = [0.1, 0.5, 0.9, 1.1, 1.5]
        self.assertEqual(threshold_probability(vals, 1.0, "above"), 0.4)

    def test_threshold_probability_below(self):
        vals = [0.1, 0.5, 0.9, 1.1, 1.5]
        self.assertEqual(threshold_probability(vals, 1.0, "below"), 0.6)

    def test_sensitivity_ordering(self):
        base = {"a": 1.0, "b": 1.0}
        def f(d): return d["a"] * 2 + d["b"]
        s = sensitivity(base, f, {"a": 0.1, "b": 0.1}, seed=0)
        # a has double the impact of b
        keys = [t[0] for t in s[:2]]
        self.assertEqual(keys[0], "a")

    def test_is_finite_number(self):
        self.assertTrue(is_finite_number(1.0))
        self.assertTrue(is_finite_number(0))
        self.assertFalse(is_finite_number(float("inf")))
        self.assertFalse(is_finite_number(float("nan")))
        self.assertFalse(is_finite_number(True))


if __name__ == "__main__":
    unittest.main()
