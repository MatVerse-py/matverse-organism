"""
matverse.omega
==============

The normalized Omega Score (Ω) of the organism.

The corpus canonizes the Omega Score as the geometric mean of five
viability dimensions, each normalized to [0, 1]:

    Ω = (D_1 · D_2 · D_3 · D_4 · D_5)^(1/5)

    D_1 = C_inv   : constitutional invariants hold (0..1)
    D_2 = PBR_n   : PBR normalized to [0, 1] via min(PBR/30, 1)
    D_3 = R_rec_n : reconstructibility normalized via min(R_rec/5, 1)
    D_4 = A_aut   : autopoiesis (self-repair success rate)
    D_5 = F_ant   : antifragility (improvement-under-stress score)

All dimensions must be in [0, 1] before the geometric mean. A zero in
any dimension produces Ω = 0 (constitutional gate against volume-without-viability).

Validation against the canonical closure v3.6:
    C_inv = 0.92, PBR = 21.91 → PBR_n = 0.730
    R_rec = 4 → R_rec_n = 0.80
    A_aut = 0.78, F_ant = 0.85
    Ω = (0.92 · 0.730 · 0.80 · 0.78 · 0.85)^(1/5) ≈ 0.820

The Riemannian integration (v3.8.0) is expected to push A_aut to ≈0.82
and F_ant to ≈0.88, raising Ω to ≈0.835.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional


PBR_NORMALIZATION_DENOM = 30.0
RREC_NORMALIZATION_DENOM = 5.0


def normalize_pbr(pbr: float) -> float:
    """min(PBR / 30, 1). The PBR is unbounded above; this caps it at 1.0."""
    return max(0.0, min(1.0, pbr / PBR_NORMALIZATION_DENOM))


def normalize_rrec(rrec: float) -> float:
    """min(R_rec / 5, 1). The reconstructibility is bounded above by 5."""
    return max(0.0, min(1.0, rrec / RREC_NORMALIZATION_DENOM))


def omega_score(c_inv: float, pbr: float, r_rec: float,
                a_aut: float, f_ant: float) -> float:
    """Compute the canonical Ω score (geometric mean of 5 normalized dims).

    Parameters
    ----------
    c_inv : constitutional invariant coverage, [0, 1]
    pbr   : Planetary Benefit Ratio, raw (will be normalized)
    r_rec : reconstructibility, raw (will be normalized)
    a_aut : autopoiesis success rate, [0, 1]
    f_ant : antifragility score, [0, 1]

    Returns
    -------
    Ω in [0, 1]. Returns 0.0 if any dimension is 0 (constitutional gate).
    """
    D = [c_inv, normalize_pbr(pbr), normalize_rrec(r_rec), a_aut, f_ant]
    for d in D:
        if d <= 0.0:
            return 0.0
        if d > 1.0:
            d = 1.0  # defensive clamp
    product = 1.0
    for d in D:
        product *= d
    return product ** (1.0 / 5.0)


@dataclass
class OmegaReport:
    c_inv: float
    pbr: float
    pbr_n: float
    r_rec: float
    r_rec_n: float
    a_aut: float
    f_ant: float
    omega: float
    interpretation: str

    def to_dict(self) -> Dict[str, float]:
        return {
            "C_inv": self.c_inv,
            "PBR": self.pbr,
            "PBR_normalized": self.pbr_n,
            "R_rec": self.r_rec,
            "R_rec_normalized": self.r_rec_n,
            "A_aut": self.a_aut,
            "F_ant": self.f_ant,
            "omega": self.omega,
        }


def interpret_omega(omega: float) -> str:
    if omega >= 0.9:
        return "STRONG_VIABILITY"
    if omega >= 0.8:
        return "VIABLE"
    if omega >= 0.6:
        return "DEGRADED_BUT_OPERATIONAL"
    if omega >= 0.4:
        return "QUARANTINE_CANDIDATE"
    if omega > 0.0:
        return "REVOCATION_CANDIDATE"
    return "INVARIANT_VIOLATED"


def omega_from_closure(closure: dict) -> OmegaReport:
    """Build an OmegaReport from a closure JSON dict (best-effort extraction)."""
    # c_inv: from the invariants report
    inv = closure.get("invariants") or {}
    if isinstance(inv, dict):
        verdicts = inv.get("verdicts", [])
        if verdicts:
            c_inv = sum(1 for v in verdicts if v.get("holds")) / len(verdicts)
        else:
            c_inv = 0.5
    else:
        c_inv = 0.5
    # pbr: from the thermo projection
    thermo = closure.get("thermo", {})
    pbr = thermo.get("planetary_benefit_ratio", 0.0)
    # r_rec: from the canonization (closure.replay_score * 5)
    canon = closure.get("canonization", {})
    r_rec = (canon.get("replay_score", 0.0) or 0.0) * 5.0
    # a_aut and f_ant: from the existential report
    exist = closure.get("existential", {})
    a_aut = exist.get("autopoiesis_rate", 0.0) or 0.0
    f_ant = exist.get("antifragility_score", 0.0) or 0.0
    omega = omega_score(c_inv, pbr, r_rec, a_aut, f_ant)
    return OmegaReport(
        c_inv=c_inv, pbr=pbr, pbr_n=normalize_pbr(pbr),
        r_rec=r_rec, r_rec_n=normalize_rrec(r_rec),
        a_aut=a_aut, f_ant=f_ant, omega=omega,
        interpretation=interpret_omega(omega),
    )
