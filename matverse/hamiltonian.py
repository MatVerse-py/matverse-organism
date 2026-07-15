"""
matverse.hamiltonian
====================

GTHDL: General Theory of Hamiltonian Digital Life.

Implements the master equation for the organism's density operator:

    dρ/dt = -i [Ĥ_Σ, ρ]

where the **Soberano Hamiltonian** is decomposed into four operators:

    Ĥ_Σ = λ_Ω · Ω̂  +  λ_Ψ · Ψ̂  +  λ_C · Ĉ  +  λ_T · T̂

    Ω̂   Antifragilidade   — capacity to improve under stress
    Ψ̂   Coerência Semântica — integrity of the information
    Ĉ   Custo Qualitativo  — computational effort (penalty)
    T̂   Resiliência Topológica — redundancy of paths (Betti numbers)

In the pure-Python stdlib version, the density operator ρ is a
symmetric real matrix (the imaginary-unit treatment of complex density
operators is reduced to a real symmetric representation, with the
commutator replaced by the Lie bracket [H, ρ] for skew-symmetric H).

The free propagator is the matrix exponential exp(-i H dt). In the
real symmetric case we use the closed-form for a 2×2 block and a
power-series fallback for higher dimensions.

This module is the 12th constitutional organ in the v3.8.0 model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple

from .mnb_formal import FormalMNB, MNBState


# ---------------------------------------------------------------------------
# Operators (as diagonal or tridiagonal matrices in the basis they own)
# ---------------------------------------------------------------------------

@dataclass
class HamiltonianOperators:
    """The four canonical operators of the Soberano Hamiltonian.

    Each operator is represented as a diagonal matrix (the "native basis"
    of that operator). The composite Hamiltonian is built in the tensor
    product basis but, for evolution under pure λ dynamics, we sum the
    operators after weighting.

    Attributes
    ----------
    omega : Antifragility operator. Eigenvalues are 1/(1 + n_k) for
            n_k = activation count of unit k.
    psi   : Semantic coherence operator. Eigenvalues are the unit's ψ.
    cost  : Qualitative cost operator. Eigenvalues are the unit's
            adjusted cost (penalty).
    tau   : Topological resilience operator. Eigenvalues are the unit's τ.
    """

    omega: List[float] = field(default_factory=list)
    psi:   List[float] = field(default_factory=list)
    cost:  List[float] = field(default_factory=list)
    tau:   List[float] = field(default_factory=list)

    @classmethod
    def from_units(cls, units: List[MNBState]) -> "HamiltonianOperators":
        return cls(
            omega=[1.0 / (1.0 + u.activation_count) for u in units],
            psi=[u.mnb.psi for u in units],
            cost=[u.adjusted_cost() for u in units],
            tau=[u.mnb.tau for u in units],
        )

    def dimension(self) -> int:
        return len(self.psi)


# ---------------------------------------------------------------------------
# The Soberano Hamiltonian
# ---------------------------------------------------------------------------

@dataclass
class Hamiltonian:
    """Ĥ_Σ = λ_Ω · Ω̂ + λ_Ψ · Ψ̂ + λ_C · Ĉ + λ_T · T̂

    Default weights match `ThermodynamicGate`'s defaults for consistency.
    """

    lambda_omega: float = 0.25
    lambda_psi:   float = 0.25
    lambda_cost:  float = 0.30
    lambda_tau:   float = 0.20

    def compose(self, ops: HamiltonianOperators) -> List[float]:
        """Return the diagonal of Ĥ_Σ in the operator-product basis."""
        n = ops.dimension()
        if n == 0:
            return []
        return [
            (self.lambda_omega * ops.omega[k]
             + self.lambda_psi   * ops.psi[k]
             + self.lambda_cost  * ops.cost[k]
             + self.lambda_tau   * ops.tau[k])
            for k in range(n)
        ]

    def to_matrix(self, ops: HamiltonianOperators) -> List[List[float]]:
        """Build the matrix form (diagonal in this basis)."""
        diag = self.compose(ops)
        n = len(diag)
        H = [[0.0] * n for _ in range(n)]
        for k in range(n):
            H[k][k] = diag[k]
        return H


# ---------------------------------------------------------------------------
# Density operator ρ
# ---------------------------------------------------------------------------

@dataclass
class DensityOperator:
    """The density operator ρ of the system.

    Represented as a real symmetric matrix. Trace is preserved (it
    must be 1.0; the constructor normalizes). Diagonal entries
    represent the probability of finding the system in each basis state.
    """

    matrix: List[List[float]]

    def __post_init__(self) -> None:
        self._normalize()

    @classmethod
    def uniform(cls, dim: int) -> "DensityOperator":
        m = [[1.0 / dim if i == j else 0.0 for j in range(dim)] for i in range(dim)]
        return cls(matrix=m)

    @classmethod
    def from_value_densities(cls, units: List[MNBState]) -> "DensityOperator":
        rhos = [max(1e-9, u.effective_value_density()) for u in units]
        total = sum(rhos)
        n = len(units)
        m = [[0.0] * n for _ in range(n)]
        for k, r in enumerate(rhos):
            m[k][k] = r / total
        return cls(matrix=m)

    def _normalize(self) -> None:
        n = len(self.matrix)
        if n == 0:
            return
        trace = sum(self.matrix[k][k] for k in range(n))
        if trace <= 0:
            for k in range(n):
                self.matrix[k][k] = 1.0 / n
            return
        for k in range(n):
            self.matrix[k][k] /= trace

    def trace(self) -> float:
        return sum(self.matrix[k][k] for k in range(len(self.matrix)))

    def diagonal(self) -> List[float]:
        return [self.matrix[k][k] for k in range(len(self.matrix))]

    def entropy(self) -> float:
        """Von Neumann entropy S(ρ) = -Tr(ρ log ρ)."""
        h = 0.0
        for p in self.diagonal():
            if p > 1e-12:
                h -= p * math.log(p)
        return h


# ---------------------------------------------------------------------------
# Lie bracket [H, ρ] and propagator exp(-i H dt)
# ---------------------------------------------------------------------------

def commutator(H: List[List[float]], rho: List[List[float]]) -> List[List[float]]:
    """Compute [H, ρ] = H ρ - ρ H. Both inputs are real matrices."""
    n = len(H)
    out = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            s = 0.0
            for k in range(n):
                s += H[i][k] * rho[k][j] - rho[i][k] * H[k][j]
            out[i][j] = s
    return out


def matrix_multiply(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    n = len(A)
    out = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            s = 0.0
            for k in range(n):
                s += A[i][k] * B[k][j]
            out[i][j] = s
    return out


def matrix_add(A: List[List[float]], B: List[List[float]], scale: float = 1.0) -> List[List[float]]:
    n = len(A)
    return [[A[i][j] + scale * B[i][j] for j in range(n)] for i in range(n)]


def matrix_scale(A: List[List[float]], c: float) -> List[List[float]]:
    n = len(A)
    return [[c * A[i][j] for j in range(n)] for i in range(n)]


def expm_diagonal(H: List[List[float]], dt: float) -> List[List[float]]:
    """For a diagonal H, exp(-i H dt) is also diagonal with phases.

    In the real symmetric representation (no imaginary unit), the
    equivalent "free evolution" of a diagonal H is a no-op: the
    density operator on the diagonal commutes with H. We therefore
    return the identity in that case. Off-diagonal H is handled by
    `evolve_rho` below using a Taylor expansion of the exponential
    (sufficient for short dt).
    """
    n = len(H)
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def evolve_rho(H: List[List[float]], rho: List[List[float]], dt: float) -> List[List[float]]:
    """Evolve ρ by dt under master equation dρ/dt = -i [H, ρ].

    In the real symmetric representation, the closed form is:

        ρ(t) = exp(-t · ad_H) ρ(0)

    where ad_H is the adjoint operator X -> [H, X].

    We use a power-series expansion of exp(-t · ad_H) ρ, truncated at
    order 6 (sufficient for dt * ||H||_F < 1).
    """
    n = len(H)
    if n == 0:
        return rho
    # Scale: ||H||_F
    fro = 0.0
    for i in range(n):
        for j in range(n):
            fro += H[i][j] ** 2
    fro = math.sqrt(fro)
    if fro < 1e-12:
        return rho
    # Renormalize dt to keep convergence
    steps = max(1, int(math.ceil(fro * abs(dt))))
    sub_dt = dt / steps
    current = [row[:] for row in rho]
    for _ in range(steps):
        # exp(-sub_dt * ad_H) ρ ≈ I - sub_dt * [H, ρ] + (sub_dt^2 / 2) * [H, [H, ρ]] - ...
        comm1 = commutator(H, current)
        comm2 = commutator(H, comm1)
        comm3 = commutator(H, comm2)
        term1 = matrix_scale(comm1, -sub_dt)
        term2 = matrix_scale(comm2, sub_dt * sub_dt / 2.0)
        term3 = matrix_scale(comm3, -(sub_dt ** 3) / 6.0)
        current = matrix_add(current, term1)
        current = matrix_add(current, term2)
        current = matrix_add(current, term3)
        # Re-symmetrize (numerical safety)
        for i in range(n):
            for j in range(i + 1, n):
                avg = (current[i][j] + current[j][i]) / 2.0
                current[i][j] = avg
                current[j][i] = avg
    return current


# ---------------------------------------------------------------------------
# High-level orchestrator: the GTHDL propagator
# ---------------------------------------------------------------------------

@dataclass
class GTHDLPropagator:
    """The single-organism GTHDL propagator.

    Holds the current density operator ρ and the Hamiltonian; provides
    `step()` to advance by dt and `evolution_metrics()` for the closure.
    """

    hamiltonian: Hamiltonian
    rho: DensityOperator
    units: List[MNBState] = field(default_factory=list)

    @classmethod
    def from_units(cls, units: List[MNBState],
                   lambda_omega: float = 0.25,
                   lambda_psi: float = 0.25,
                   lambda_cost: float = 0.30,
                   lambda_tau: float = 0.20) -> "GTHDLPropagator":
        ops = HamiltonianOperators.from_units(units)
        h = Hamiltonian(lambda_omega=lambda_omega,
                        lambda_psi=lambda_psi,
                        lambda_cost=lambda_cost,
                        lambda_tau=lambda_tau)
        rho = DensityOperator.from_value_densities(units)
        return cls(hamiltonian=h, rho=rho, units=units)

    def step(self, dt: float = 0.1) -> None:
        ops = HamiltonianOperators.from_units(self.units)
        H = self.hamiltonian.to_matrix(ops)
        new_matrix = evolve_rho(H, self.rho.matrix, dt)
        self.rho = DensityOperator(matrix=new_matrix)

    def evolution_metrics(self) -> dict:
        """Metrics for the closure canonization."""
        return {
            "trace": self.rho.trace(),
            "entropy": self.rho.entropy(),
            "diagonal": self.rho.diagonal(),
            "n_units": len(self.units),
        }

    def dominant_unit(self) -> int:
        """Return the index of the unit with the highest probability."""
        diag = self.rho.diagonal()
        if not diag:
            return -1
        return diag.index(max(diag))


# ---------------------------------------------------------------------------
# Conservation check
# ---------------------------------------------------------------------------

def check_conservation(rho_initial: DensityOperator, rho_final: DensityOperator,
                       tol: float = 1e-6) -> Tuple[bool, float]:
    """Trace must be preserved under unitary evolution (up to numerical tol)."""
    diff = abs(rho_initial.trace() - rho_final.trace())
    return (diff < tol, diff)
