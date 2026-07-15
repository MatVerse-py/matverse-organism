"""
matverse.mnb_formal
===================

The formal 5-tuple Mem-Nano-Bit (MNB) as defined in
"The General Theory of Hamiltonian Digital Life (GTHDL)"
(au.176523668.82838950/v2) and
"Mem-Nano-Bit (MNB): A Thermodynamic Framework for Verifiable
Cognitive Memory Units" (Arêas, 2026, DOI: 10.22541/au.176523668.82838950/v2).

The 5-tuple is the canonical object that v3.7.0's MMNB builds upon:

    m = (e, Ψ, C, τ, h)

    e  = carrier / event content (the thing being remembered)
    Ψ  = semantic coherence
    C  = thermodynamic cost
    τ  = temporal persistence
    h  = cryptographic verification hash

The **value density** is the selection criterion for memory survival:

    ρ = Ψ · τ / C

A unit survives pruning iff ρ > ρ_min (default 0.5).

This module also defines the MNBState that the v0.2 kernel uses, with
informational pruning and autopoietic regeneration, and the ThermodynamicGate
that selects the lowest-cost admissible unit under system load.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# The canonical 5-tuple
# ---------------------------------------------------------------------------

@dataclass
class FormalMNB:
    """The 5-tuple m = (e, Ψ, C, τ, h).

    e  carrier  : the content (a string, dict, or serializable object)
    Ψ  psi     : semantic coherence, in [0, 1]
    C  cost    : thermodynamic cost, > 0
    τ  tau     : temporal persistence, in [0, 1] (1 = permanent)
    h  hash    : cryptographic verification (SHA-256 of canonical e)
    """

    e: Any
    psi: float
    cost: float
    tau: float
    h: str = ""

    def __post_init__(self) -> None:
        if not (0.0 <= self.psi <= 1.0):
            raise ValueError(f"psi (Ψ) must be in [0,1], got {self.psi}")
        if self.cost <= 0:
            raise ValueError(f"cost (C) must be > 0, got {self.cost}")
        if not (0.0 <= self.tau <= 1.0):
            raise ValueError(f"tau (τ) must be in [0,1], got {self.tau}")
        if not self.h:
            self.h = self._compute_h()

    def _compute_h(self) -> str:
        canonical = json.dumps(self.e, sort_keys=True, default=str)
        return "h-" + hashlib.sha256(canonical.encode()).hexdigest()[:24]

    def value_density(self) -> float:
        """ρ = Ψ · τ / C — the selection criterion for survival.

        Higher ρ means the MNB is more valuable per unit cost.
        """
        return (self.psi * self.tau) / self.cost

    def survives_pruning(self, rho_min: float = 0.5) -> bool:
        """Informational pruning: keep iff value density > threshold.

        Default ρ_min = 0.5 is a balanced gate: a unit with high coherence
        and persistence but moderate cost is retained; an obsolete unit
        with low coherence is pruned.
        """
        return self.value_density() > rho_min

    def age(self, now: float) -> float:
        """Temporal decay (in units of τ).

        Given `now` (a unix epoch or monotonic counter) and a creation
        timestamp, returns the decayed persistence. The caller is
        responsible for the actual `created_at` field; this is the
        canonical decay function.
        """
        # Stub: requires `created_at` to be passed via the wrapping MNB
        # object (see MNBState below). Here we just return tau as a
        # conservative upper bound.
        return self.tau

    def as_tuple(self) -> Tuple[Any, float, float, float, str]:
        return (self.e, self.psi, self.cost, self.tau, self.h)

    def to_dict(self) -> Dict[str, Any]:
        return {"e": self.e, "psi": self.psi, "cost": self.cost,
                "tau": self.tau, "h": self.h, "rho": self.value_density()}

    def verify(self) -> bool:
        """Recompute h from e and compare. Catches tampering with the carrier."""
        return self.h == self._compute_h()


# ---------------------------------------------------------------------------
# MNBState — the dynamic wrapper (v0.2 kernel style)
# ---------------------------------------------------------------------------

class MNBPhase(str, Enum):
    """Lifecycle of an MNB unit (informational pruning + autopoiesis)."""
    GENESIS = "GENESIS"     # just created, no pruning yet
    STABLE  = "STABLE"      # survived at least one pruning cycle
    DEGRADED = "DEGRADED"   # ρ < ρ_min but allowed to remain
    PRUNED  = "PRUNED"      # ρ < ρ_min, removed
    REGENERATED = "REGENERATED"  # reborn from h after pruning


@dataclass
class MNBState:
    """Dynamic MNB unit with timestamp, phase, and adaptive cost.

    Wraps a FormalMNB and adds the operational state needed by the
    ThermodynamicGate and the runner: creation time, current phase,
    dynamic cost (which can be raised under load), and a usage count.
    """

    id: str
    mnb: FormalMNB
    created_at: float = field(default_factory=lambda: time.time())
    last_activated_at: float = 0.0
    activation_count: int = 0
    phase: MNBPhase = MNBPhase.GENESIS
    dynamic_cost_multiplier: float = 1.0

    def __post_init__(self) -> None:
        if not self.id:
            self.id = "MNB-" + self.mnb.h[2:14]

    def adjusted_cost(self) -> float:
        """C_adj = C · (1 + ‖R‖_local · dynamic_cost_multiplier).

        In the pure stdlib version, the curvature term is approximated
        by the dynamic_cost_multiplier (which the runner can raise
        under load or on hot regions of the Riemannian manifold).
        """
        return self.mnb.cost * (1.0 + self.dynamic_cost_multiplier * 0.1)

    def effective_value_density(self) -> float:
        return self.mnb.value_density() / max(1e-9, self.adjusted_cost())

    def should_prune(self, rho_min: float = 0.5) -> bool:
        return self.effective_value_density() < rho_min

    def tick(self, now: float) -> None:
        """Decay tau over time, mark degraded if density drops."""
        elapsed = max(0.0, now - self.created_at)
        # τ decays linearly over a default half-life of 1e6 seconds (~11.5 days)
        half_life = 1_000_000.0
        decay = max(0.0, 1.0 - elapsed / half_life)
        if decay < self.mnb.tau:
            self.mnb = FormalMNB(
                e=self.mnb.e, psi=self.mnb.psi,
                cost=self.mnb.cost, tau=decay, h=self.mnb.h,
            )
        if self.should_prune() and self.phase == MNBPhase.STABLE:
            self.phase = MNBPhase.DEGRADED

    def regenerate(self) -> None:
        """Autopoietic regeneration: rebuild from h with reduced cost."""
        new_cost = self.mnb.cost * 0.8  # 20% cost reduction
        self.mnb = FormalMNB(
            e=self.mnb.e, psi=min(1.0, self.mnb.psi * 1.05),
            cost=new_cost, tau=self.mnb.tau, h=self.mnb.h,
        )
        self.phase = MNBPhase.REGENERATED
        self.created_at = time.time()


# ---------------------------------------------------------------------------
# ThermodynamicGate — the Hamiltonian-Gate selector
# ---------------------------------------------------------------------------

@dataclass
class ThermodynamicGate:
    """Selects the MNB that minimizes the Hamiltonian of the system.

    H_Σ(unit) = λ_Ω · Ω̂(unit) + λ_Ψ · Ψ̂(unit) + λ_C · Ĉ(unit) + λ_T · T̂(unit)

    where (in this pure-stdlib, no-numpy version):
        Ω̂  ≈ 1 / (1 + activation_count)   (antifragility penalty for overuse)
        Ψ̂  = psi                            (semantic coherence)
        Ĉ  = adjusted_cost                  (qualitative cost)
        T̂  = tau                            (topological resilience)

    Default weights balance the four operators:
        λ_Ω = 0.25, λ_Ψ = 0.25, λ_C = 0.30, λ_T = 0.20
    """

    lambda_omega: float = 0.25
    lambda_psi:   float = 0.25
    lambda_cost:  float = 0.30
    lambda_tau:   float = 0.20
    rho_min:      float = 0.5

    def _omega(self, unit: MNBState) -> float:
        return 1.0 / (1.0 + unit.activation_count)

    def hamiltonian(self, unit: MNBState) -> float:
        omega = self._omega(unit)
        return (self.lambda_omega * omega
                + self.lambda_psi  * unit.mnb.psi
                + self.lambda_cost * unit.adjusted_cost()
                + self.lambda_tau  * unit.mnb.tau)

    def should_activate(self, unit: MNBState, system_load: float = 0.5) -> bool:
        if unit.phase == MNBPhase.PRUNED:
            return False
        if unit.effective_value_density() < self.rho_min:
            return False
        # Under heavy load, only units with high psi and tau may be activated
        if system_load > 0.8 and (unit.mnb.psi < 0.4 or unit.mnb.tau < 0.4):
            return False
        return True

    def force_activate_if_critical(self, unit: MNBState, system_load: float = 0.5) -> bool:
        """Bypass the gate for critical units (high psi AND high tau)."""
        return (unit.mnb.psi > 0.9 and unit.mnb.tau > 0.9
                and unit.phase != MNBPhase.PRUNED)

    def select(self, units: List[MNBState], system_load: float = 0.5) -> Optional[MNBState]:
        """Select the unit that minimizes the Hamiltonian among admissible ones.

        Returns None if no unit is admissible.
        """
        candidates = [u for u in units if self.should_activate(u, system_load)]
        if not candidates:
            return None
        return min(candidates, key=self.hamiltonian)

    def select_all(self, units: List[MNBState], system_load: float = 0.5) -> List[MNBState]:
        """Return all admissible units, sorted by Hamiltonian (lowest first)."""
        candidates = [u for u in units if self.should_activate(u, system_load)]
        candidates.sort(key=self.hamiltonian)
        return candidates


# ---------------------------------------------------------------------------
# Pruning cycle — the informational pruning operator
# ---------------------------------------------------------------------------

def prune(units: List[MNBState], rho_min: float = 0.5) -> Tuple[List[MNBState], List[MNBState]]:
    """Apply informational pruning. Returns (survivors, pruned)."""
    survivors, pruned = [], []
    for u in units:
        if u.effective_value_density() > rho_min:
            survivors.append(u)
        else:
            u.phase = MNBPhase.PRUNED
            pruned.append(u)
    return survivors, pruned


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------

def from_payload(payload: Any, psi: float = 0.8, cost: float = 1.0, tau: float = 1.0) -> MNBState:
    """Build an MNBState from a raw payload with sensible defaults."""
    mnb = FormalMNB(e=payload, psi=psi, cost=cost, tau=tau)
    return MNBState(id="", mnb=mnb)
