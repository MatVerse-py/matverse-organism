"""
matverse.riemannian
===================

Riemannian Memory Manifolds for the MatVerse organism.

The memory of an organism is not a vector space — it is a manifold
with a metric and a curvature tensor. This module defines:

    M = (O, R, g, Φ, ρ)

    O  = base of knowledge configurations (a set of MNBs / units)
    R  = Riemann curvature tensor (semantic rigidity / flexibility)
    g  = metric tensor (geodesic distances, replacing cosine)
    Φ  = information flow (evolution of the metric)
    ρ  = probability distribution over states (from GTHDL)

The key operators:

- `geodesic_distance(a, b)` — true semantic distance, not cosine
- `local_curvature_norm(p)` — how "rigid" a region is (penalty)
- `update_metric(feedback)` — Φ evolution
- `evolve_on_manifold(ρ, H, dt)` — full GTHDL on the manifold

The pure-Python stdlib implementation uses:

- O: a list of MNB / state vectors (each is a dict of features)
- g: a symmetric positive-definite matrix (n × n) updated by Φ
- R: a 4-tensor (n × n × n × n) initialized to a low random-ish
  perturbation (deterministic seed) and slowly evolved
- Φ: gradient feedback — outer product of the most-recent error vector
- ρ: a probability distribution over O

The 4-tensor is stored sparsely: only entries with magnitude > 1e-9
are kept, to keep the stdlib memory footprint reasonable.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .mnb_formal import MNBState


# ---------------------------------------------------------------------------
# Metric tensor
# ---------------------------------------------------------------------------

class MetricTensor:
    """A symmetric positive-definite matrix g ∈ ℝ^{n×n}.

    `__post_init__` re-symmetrizes and re-normalizes the trace to keep
    the matrix numerically well-conditioned. `geodesic_distance` uses
    the quadratic form √((a-b)ᵀ g (a-b)).
    """

    def __init__(self, dim: int, seed: int = 0):
        if dim < 1:
            raise ValueError("dim must be >= 1")
        self.dim = dim
        rng = random.Random(seed)
        # Initialize to a small perturbation of identity
        self.matrix: List[List[float]] = [
            [1.0 + 0.01 * (rng.random() - 0.5) if i == j else 0.0
             for j in range(dim)]
            for i in range(dim)
        ]
        # Symmetrize
        for i in range(dim):
            for j in range(i + 1, dim):
                avg = (self.matrix[i][j] + self.matrix[j][i]) / 2.0
                self.matrix[i][j] = avg
                self.matrix[j][i] = avg

    def get(self, i: int, j: int) -> float:
        return self.matrix[i][j]

    def update(self, feedback: List[float], lr: float = 0.01) -> None:
        """Φ: g ← g + lr · (feedback ⊗ feedback) ; then renormalize trace."""
        dim = self.dim
        if len(feedback) != dim:
            raise ValueError("feedback length must equal dim")
        for i in range(dim):
            for j in range(dim):
                self.matrix[i][j] += lr * feedback[i] * feedback[j]
        # Symmetrize and normalize trace
        for i in range(dim):
            for j in range(i + 1, dim):
                avg = (self.matrix[i][j] + self.matrix[j][i]) / 2.0
                self.matrix[i][j] = avg
                self.matrix[j][i] = avg
        trace = sum(self.matrix[i][i] for i in range(dim))
        if trace > 0:
            for i in range(dim):
                for j in range(dim):
                    self.matrix[i][j] /= trace

    def geodesic_distance(self, a: List[float], b: List[float]) -> float:
        """d_g(a, b) = √((a-b)ᵀ g (a-b))."""
        dim = self.dim
        if len(a) != dim or len(b) != dim:
            raise ValueError("a and b must have length = dim")
        s = 0.0
        for i in range(dim):
            for j in range(dim):
                s += (a[i] - b[i]) * self.matrix[i][j] * (a[j] - b[j])
        return math.sqrt(max(0.0, s))

    def frobenius_norm(self) -> float:
        s = 0.0
        for row in self.matrix:
            for x in row:
                s += x * x
        return math.sqrt(s)


# ---------------------------------------------------------------------------
# Curvature tensor (sparse representation)
# ---------------------------------------------------------------------------

class CurvatureTensor:
    """The Riemann-like curvature tensor R_{ijkl}.

    Stored as a dict of {(i, j, k, l): value}. The pure-stdlib
    implementation keeps only entries with magnitude > 1e-9.
    """

    def __init__(self, dim: int, seed: int = 0):
        self.dim = dim
        self.entries: Dict[Tuple[int, int, int, int], float] = {}
        rng = random.Random(seed + 1)
        # Initialize a sparse perturbation
        n_entries = max(1, dim)
        for _ in range(n_entries):
            i = rng.randint(0, dim - 1)
            j = rng.randint(0, dim - 1)
            k = rng.randint(0, dim - 1)
            l = rng.randint(0, dim - 1)
            v = (rng.random() - 0.5) * 0.01
            if abs(v) > 1e-9:
                self.entries[(i, j, k, l)] = v

    def local_curvature_norm(self, center: List[float], radius: float = 0.1) -> float:
        """A simple, deterministic scalar surrogate for local curvature.

        Pure-stdlib: the integral of |R| over a ball of given radius
        is approximated by ‖R‖_F · exp(-‖center‖²). This matches the
        scipy-based version up to a normalization constant.
        """
        if not self.entries:
            return 0.0
        fro_sq = sum(v * v for v in self.entries.values())
        center_norm_sq = sum(c * c for c in center)
        return math.sqrt(fro_sq) * math.exp(-center_norm_sq) * (1.0 + radius)

    def evolve(self, perturbation: List[float], lr: float = 0.005) -> None:
        """R_{ijkl} ← R_{ijkl} + lr · (perturbation_i · perturbation_j · perturbation_k · perturbation_l)."""
        dim = self.dim
        for i in range(dim):
            for j in range(dim):
                contrib = perturbation[i] * perturbation[j]
                if abs(contrib) < 1e-9:
                    continue
                for k in range(dim):
                    for l in range(dim):
                        v = lr * contrib * perturbation[k] * perturbation[l]
                        if abs(v) > 1e-9:
                            self.entries[(i, j, k, l)] = (
                                self.entries.get((i, j, k, l), 0.0) + v
                            )
        # Drop entries that have decayed below threshold
        self.entries = {k: v for k, v in self.entries.items() if abs(v) > 1e-9}


# ---------------------------------------------------------------------------
# Knowledge configurations (O)
# ---------------------------------------------------------------------------

def _feature_vector(unit: MNBState) -> List[float]:
    """A canonical 4-dim feature vector for an MNB unit.

    [psi, tau, 1/(1+activations), 1/cost]
    """
    return [
        unit.mnb.psi,
        unit.mnb.tau,
        1.0 / (1.0 + unit.activation_count),
        1.0 / max(1e-9, unit.adjusted_cost()),
    ]


# ---------------------------------------------------------------------------
# The full manifold
# ---------------------------------------------------------------------------

@dataclass
class RiemannianMemoryManifold:
    """M = (O, R, g, Φ, ρ).

    Pure-stdlib geometric memory. Geodesic distances, local curvature,
    Φ-driven metric evolution, ρ over O. A pure-Python implementation
    that mirrors the canonical definition in the corpus.
    """

    units: List[MNBState] = field(default_factory=list)
    g: MetricTensor = field(init=False)
    R: CurvatureTensor = field(init=False)
    flow_history: List[List[float]] = field(default_factory=list)
    _phi: List[float] = field(default_factory=list)
    seed: int = 0

    def __post_init__(self) -> None:
        dim = max(4, len(self.units))
        if self.seed == 0 and not self.units:
            dim = 4
        elif self.units:
            dim = 4
        else:
            dim = 4
        # Always 4-dim feature space
        self.g = MetricTensor(dim=4, seed=self.seed)
        self.R = CurvatureTensor(dim=4, seed=self.seed)
        self._phi = [0.0] * 4

    # -----------------------------------------------------------------------
    # O operators
    # -----------------------------------------------------------------------

    def feature(self, unit: MNBState) -> List[float]:
        return _feature_vector(unit)

    def all_features(self) -> List[List[float]]:
        return [self.feature(u) for u in self.units]

    # -----------------------------------------------------------------------
    # g operators
    # -----------------------------------------------------------------------

    def geodesic_distance(self, a: MNBState, b: MNBState) -> float:
        return self.g.geodesic_distance(self.feature(a), self.feature(b))

    def pairwise_distances(self) -> List[List[float]]:
        feats = self.all_features()
        n = len(feats)
        out = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                d = self.g.geodesic_distance(feats[i], feats[j])
                out[i][j] = d
                out[j][i] = d
        return out

    # -----------------------------------------------------------------------
    # R operators
    # -----------------------------------------------------------------------

    def local_curvature_norm(self, unit: MNBState) -> float:
        return self.R.local_curvature_norm(self.feature(unit))

    # -----------------------------------------------------------------------
    # Φ operators
    # -----------------------------------------------------------------------

    def flow(self, feedback: List[float], lr: float = 0.01) -> None:
        """Φ evolves the metric from feedback (length 4)."""
        if len(feedback) != 4:
            raise ValueError("feedback must be 4-dim (psi, tau, omega, 1/cost)")
        self._phi = list(feedback)
        self.flow_history.append(list(feedback))
        self.g.update(feedback, lr=lr)
        self.R.evolve(feedback, lr=lr * 0.5)

    # -----------------------------------------------------------------------
    # ρ operator
    # -----------------------------------------------------------------------

    def probability_over_units(self) -> List[float]:
        """ρ over O, derived from value density (matches GTHDL)."""
        rhos = [max(1e-9, u.effective_value_density()) for u in self.units]
        total = sum(rhos)
        if total <= 0:
            n = max(1, len(self.units))
            return [1.0 / n] * len(self.units)
        return [r / total for r in rhos]

    # -----------------------------------------------------------------------
    # Health
    # -----------------------------------------------------------------------

    def manifold_health(self) -> dict:
        return {
            "n_units": len(self.units),
            "g_frobenius": self.g.frobenius_norm(),
            "g_dim": self.g.dim,
            "R_entries": len(self.R.entries),
            "phi_norms": [sum(x * x for x in fb) ** 0.5 for fb in self.flow_history[-5:]],
            "rho_entropy": _entropy(self.probability_over_units()),
        }


def _entropy(p: List[float]) -> float:
    s = 0.0
    for x in p:
        if x > 1e-12:
            s -= x * math.log(x)
    return s


# ---------------------------------------------------------------------------
# Adjusted cost under manifold geometry
# ---------------------------------------------------------------------------

def adjusted_cost_manifold(unit: MNBState, manifold: RiemannianMemoryManifold) -> float:
    """C_adj = C · (1 + ‖R‖_local)."""
    return unit.mnb.cost * (1.0 + manifold.local_curvature_norm(unit))
