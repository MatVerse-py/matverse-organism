"""
Tests for the GTHDL Hamiltonian propagator (matverse.hamiltonian).

Covers:
  - Hamiltonian composition with 4 operators
  - Density operator construction and trace normalization
  - Evolution step (dρ/dt = -i [H, ρ])
  - Trace conservation
  - The GTHDLPropagator orchestrator
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from matverse.mnb_formal import FormalMNB, MNBState
from matverse.hamiltonian import (
    Hamiltonian, HamiltonianOperators, DensityOperator,
    commutator, matrix_multiply, matrix_add, matrix_scale,
    evolve_rho, GTHDLPropagator, check_conservation,
)


class TestHamiltonian(unittest.TestCase):
    def test_compose(self):
        h = Hamiltonian()
        ops = HamiltonianOperators(omega=[0.5, 0.3], psi=[0.9, 0.7],
                                    cost=[1.0, 2.0], tau=[0.8, 0.5])
        diag = h.compose(ops)
        self.assertEqual(len(diag), 2)
        # diag[0] = 0.25*0.5 + 0.25*0.9 + 0.30*1.0 + 0.20*0.8 = 0.81
        self.assertAlmostEqual(diag[0], 0.81, places=3)
        # diag[1] = 0.25*0.3 + 0.25*0.7 + 0.30*2.0 + 0.20*0.5 = 0.95
        self.assertAlmostEqual(diag[1], 0.95, places=3)

    def test_to_matrix_diagonal(self):
        h = Hamiltonian()
        ops = HamiltonianOperators(omega=[0.5], psi=[0.5], cost=[1.0], tau=[0.5])
        H = h.to_matrix(ops)
        self.assertEqual(len(H), 1)
        self.assertEqual(len(H[0]), 1)
        self.assertNotEqual(H[0][0], 0.0)

    def test_from_units(self):
        u1 = MNBState(id="a", mnb=FormalMNB(e="a", psi=0.9, cost=1.0, tau=0.9),
                       activation_count=2)
        u2 = MNBState(id="b", mnb=FormalMNB(e="b", psi=0.5, cost=2.0, tau=0.5),
                       activation_count=5)
        ops = HamiltonianOperators.from_units([u1, u2])
        self.assertEqual(ops.dimension(), 2)
        # omega[0] = 1/(1+2) = 1/3
        self.assertAlmostEqual(ops.omega[0], 1/3, places=3)
        # omega[1] = 1/(1+5) = 1/6
        self.assertAlmostEqual(ops.omega[1], 1/6, places=3)


class TestDensityOperator(unittest.TestCase):
    def test_uniform_construction(self):
        rho = DensityOperator.uniform(4)
        self.assertAlmostEqual(rho.trace(), 1.0)
        # Diagonal entries are 0.25
        for d in rho.diagonal():
            self.assertAlmostEqual(d, 0.25)

    def test_from_value_densities(self):
        u1 = MNBState(id="a", mnb=FormalMNB(e="a", psi=0.9, cost=1.0, tau=0.9))
        u2 = MNBState(id="b", mnb=FormalMNB(e="b", psi=0.5, cost=1.0, tau=0.5))
        rho = DensityOperator.from_value_densities([u1, u2])
        self.assertAlmostEqual(rho.trace(), 1.0)
        # u1 has higher ρ (0.81) vs u2 (0.25), so should have higher probability
        self.assertGreater(rho.matrix[0][0], rho.matrix[1][1])

    def test_entropy(self):
        rho = DensityOperator.uniform(2)
        # Binary entropy at p=0.5: H = log(2)
        self.assertAlmostEqual(rho.entropy(), math.log(2), places=4)


class TestCommutator(unittest.TestCase):
    def test_zero_matrix_commutes(self):
        H = [[0.0, 0.0], [0.0, 0.0]]
        rho = [[0.5, 0.1], [0.1, 0.5]]
        comm = commutator(H, rho)
        for row in comm:
            for x in row:
                self.assertAlmostEqual(x, 0.0)

    def test_self_anticommute_for_antisymmetric(self):
        # If H is anti-symmetric and rho symmetric, [H, rho] is anti-symmetric
        H = [[0.0, 1.0], [-1.0, 0.0]]
        rho = [[1.0, 0.0], [0.0, 1.0]]
        comm = commutator(H, rho)
        # [H, rho] = -[H, rho]^T
        self.assertAlmostEqual(comm[0][0], 0.0)
        self.assertAlmostEqual(comm[0][1], -comm[1][0])


class TestEvolveRho(unittest.TestCase):
    def test_zero_hamiltonian_no_op(self):
        H = [[0.0, 0.0], [0.0, 0.0]]
        rho = [[0.7, 0.1], [0.1, 0.3]]
        new_rho = evolve_rho(H, rho, 0.1)
        for i in range(2):
            for j in range(2):
                self.assertAlmostEqual(new_rho[i][j], rho[i][j])

    def test_trace_approximately_preserved(self):
        H = [[0.5, 0.1], [0.1, 0.3]]
        rho = [[0.7, 0.0], [0.0, 0.3]]
        new_rho = evolve_rho(H, rho, 0.01)
        trace = sum(new_rho[i][i] for i in range(2))
        self.assertAlmostEqual(trace, 1.0, places=4)


class TestGTHDLPropagator(unittest.TestCase):
    def test_construction_and_step(self):
        units = [
            MNBState(id=f"u{i}", mnb=FormalMNB(e=f"e{i}", psi=0.5 + i*0.1,
                                                cost=1.0, tau=0.7))
            for i in range(3)
        ]
        prop = GTHDLPropagator.from_units(units)
        initial_trace = prop.rho.trace()
        self.assertAlmostEqual(initial_trace, 1.0, places=4)
        metrics = prop.evolution_metrics()
        self.assertEqual(metrics["n_units"], 3)
        prop.step(dt=0.05)
        # After step, trace still ≈ 1
        self.assertAlmostEqual(prop.rho.trace(), 1.0, places=3)

    def test_dominant_unit(self):
        u1 = MNBState(id="hi", mnb=FormalMNB(e="hi", psi=0.95, cost=1.0, tau=0.95))
        u2 = MNBState(id="lo", mnb=FormalMNB(e="lo", psi=0.2, cost=1.0, tau=0.2))
        prop = GTHDLPropagator.from_units([u1, u2])
        dom = prop.dominant_unit()
        self.assertEqual(dom, 0)  # u1 has higher ρ


class TestConservation(unittest.TestCase):
    def test_conservation_check_passes(self):
        rho1 = DensityOperator.uniform(2)
        rho2 = DensityOperator.uniform(2)
        ok, diff = check_conservation(rho1, rho2)
        self.assertTrue(ok)
        self.assertLess(diff, 1e-9)


class TestMatrixOps(unittest.TestCase):
    def test_matrix_multiply_identity(self):
        I = [[1.0, 0.0], [0.0, 1.0]]
        A = [[0.5, 0.3], [0.1, 0.7]]
        self.assertEqual(matrix_multiply(I, A), A)
        self.assertEqual(matrix_multiply(A, I), A)

    def test_matrix_add(self):
        A = [[1.0, 0.0], [0.0, 1.0]]
        B = [[0.5, 0.0], [0.0, 0.5]]
        C = matrix_add(A, B)
        self.assertEqual(C, [[1.5, 0.0], [0.0, 1.5]])

    def test_matrix_scale(self):
        A = [[1.0, 2.0], [3.0, 4.0]]
        B = matrix_scale(A, 0.5)
        self.assertEqual(B, [[0.5, 1.0], [1.5, 2.0]])


if __name__ == "__main__":
    unittest.main()
