"""
matverse.canonical
==================

12-organism constitutional taxonomy of the MatVerse organism (v3.8.0).

The 12 constitutional organs, in the canonical cycle order:

  1. MMNB                  — causal memory (the seed of the next cycle)
  2. Cassandra / MetaCortex — cognitive interpretation + level-3 learning
  3. COG (Campo de Hipóteses) — hypothesis field
  4. Invariants             — fail-closed constitutional gate
  5. Laws                   — versioned operational policies
  6. UMJAM                  — admissible mutation
  7. SVCA                   — application video-capsule (proof bundle)
  8. Closure                — closure compiler (v3.0 + v3.6 macro)
  9. Atlas                  — live cartographic projection
 10. Thermodynamic Cortex   — energy / PBR / regenerative accounting
 11. Captals                — continuity allocator + M-bit + proof chain
 12. Existential Processes  — metabolism, autopoiesis, apoptosis,
                              antifragility, homeostasis

v3.8.0 adds three new canonical objects that sit *above* the cycle:

  - GTHDL Hamiltonian       (matverse.hamiltonian)
  - Riemannian Memory Manifold (matverse.riemannian)
  - Epistemic State Machine (matverse.epistemic)

These are the *constitutional physics* of the organism — the laws
under which the 12 organs operate.

The Omega Score (matverse.omega) is the single scalar that summarizes
the viability of the whole cycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

# The 12 constitutional organs, in canonical cycle order
CONSTITUTIONAL_ORGANS_V3_8: List[str] = [
    "MMNB",                  # 1.  causal memory
    "CASSANDRA_METACORTEX",  # 2.  cognitive interpretation + L3 learning
    "COG",                   # 3.  hypothesis field (Campo de Hipóteses)
    "INVARIANTS",            # 4.  fail-closed constitutional gate
    "LAWS",                  # 5.  versioned operational policies
    "UMJAM",                 # 6.  admissible mutation
    "SVCA",                  # 7.  proof capsule
    "CLOSURE",               # 8.  closure compiler
    "ATLAS",                 # 9.  live cartographic projection
    "THERMO_CORTEX",         # 10. energy / PBR / regenerative accounting
    "CAPTALS",               # 11. continuity allocator + M-bit
    "EXISTENTIAL",           # 12. metabolism / autopoiesis / apoptosis /
                             #     antifragility / homeostasis
]

# The 3 constitutional-physics objects (v3.8.0)
CONSTITUTIONAL_PHYSICS_V3_8: List[str] = [
    "GTHDL_HAMILTONIAN",     # dρ/dt = -i [Ĥ_Σ, ρ]
    "RIEMANNIAN_MANIFOLD",   # M = (O, R, g, Φ, ρ)
    "EPISTEMIC_STATE",       # 8-state machine + Dempster-Shafer + Dung
]


@dataclass
class ConstitutionalState:
    """The constitutional state of the organism at a given moment."""
    n_organs: int = 12
    n_physics: int = 3
    organs_present: List[str] = field(default_factory=lambda: list(CONSTITUTIONAL_ORGANS_V3_8))
    physics_present: List[str] = field(default_factory=lambda: list(CONSTITUTIONAL_PHYSICS_V3_8))
    omega: float = 0.0
    cycle_position: int = 0  # 0..11 in the canonical cycle

    def is_constitutionally_complete(self) -> bool:
        return (len(self.organs_present) >= self.n_organs
                and len(self.physics_present) >= self.n_physics
                and self.omega > 0.5)

    def to_dict(self) -> dict:
        return {
            "n_organs": self.n_organs,
            "n_physics": self.n_physics,
            "organs_present": list(self.organs_present),
            "physics_present": list(self.physics_present),
            "omega": self.omega,
            "cycle_position": self.cycle_position,
            "constitutionally_complete": self.is_constitutionally_complete(),
        }


def next_organ(current: str) -> Optional[str]:
    """Return the next organ in the cycle, or None if `current` is the last."""
    if current not in CONSTITUTIONAL_ORGANS_V3_8:
        return None
    idx = CONSTITUTIONAL_ORGANS_V3_8.index(current)
    if idx + 1 >= len(CONSTITUTIONAL_ORGANS_V3_8):
        return None
    return CONSTITUTIONAL_ORGANS_V3_8[idx + 1]
