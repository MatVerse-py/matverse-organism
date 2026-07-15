"""
matverse.captals
================

Captals — the system's continuity allocator, not a public currency.

Three layers of "value" in the MatVerse organism, separated for
constitutional clarity:

  1. MNB   — causal, informational. Not an asset.
  2. Mem-bit — proof certificate. Verifiable, sometimes transferable.
  3. M-bit — calculated contribution: a vector of (compute, evidence,
              reproducibility, utility, transferability, risk, alignment).
  4. CAPT  — optional transferable unit of the eventual DAO.
  5. LCU   — LLM Compute Unit: an internal accounting of resource
              consumption. Not an economic instrument.

Emission rule (proposed, not validated):

    M_t = V_t * Q_t * R_t * T_t * A_t

where V=observed value, Q=evidence quality, R=reproducibility,
T=transferability, A=constitutional admissibility. If any factor is 0,
M_t = 0. This prevents rewarding volume without utility.

Use of CAPT as a public, transferable token requires:
  - independent legal review per jurisdiction
  - a finalized tokenomics design (HOLD in v3.5.0)
  - deployed smart contracts (NOT_IMPLEMENTED in v3.5.0)
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# LCU — LLM Compute Unit (accounting only)
# ---------------------------------------------------------------------------

@dataclass
class LCUAccount:
    """Track LCU consumption. Pure accounting; not transferable."""
    in_tokens: int = 0
    out_tokens: int = 0
    cpu_seconds: float = 0.0
    gpu_seconds: float = 0.0
    energy_wh: float = 0.0

    def add(self, other: "LCUAccount") -> None:
        self.in_tokens += other.in_tokens
        self.out_tokens += other.out_tokens
        self.cpu_seconds += other.cpu_seconds
        self.gpu_seconds += other.gpu_seconds
        self.energy_wh += other.energy_wh

    def total(self, kappa: float = 3.0,
              alpha: float = 1.0, beta: float = 5.0, gamma: float = 1.0) -> float:
        """LCU = N_in + kappa * N_out + alpha * T_cpu + beta * T_gpu + gamma * E.

        kappa, alpha, beta, gamma are tunable weights. Defaults are
        illustrative and not validated.
        """
        return (
            self.in_tokens
            + kappa * self.out_tokens
            + alpha * self.cpu_seconds
            + beta * self.gpu_seconds
            + gamma * self.energy_wh
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "in_tokens": self.in_tokens,
            "out_tokens": self.out_tokens,
            "cpu_seconds": round(self.cpu_seconds, 4),
            "gpu_seconds": round(self.gpu_seconds, 4),
            "energy_wh": round(self.energy_wh, 4),
        }


# ---------------------------------------------------------------------------
# M-bit — contribution vector
# ---------------------------------------------------------------------------

@dataclass
class MBit:
    """A calculated contribution. NOT a public token. NOT a price.

    The M-bit is the evidence that *some* useful work happened in a
    verifiable way. Its six dimensions are the corpus proposal.
    """
    work_id: str
    contributor: str
    compute_cost: float = 0.0
    evidence_quality: float = 0.0
    reproducibility: float = 0.0
    utility: float = 0.0
    transferability: float = 0.0
    risk: float = 0.0
    human_alignment: float = 0.0
    status: str = "DECLARED"           # DECLARED | ADMISSIBLE_CONTRIBUTION | REJECTED
    proofs: Dict[str, str] = field(default_factory=dict)   # PoSE, PoCT, PoTM, PoLE

    def geometric_score(self) -> float:
        """Geometric mean of the six positive dimensions times (1 - CVaR-like risk)."""
        dims = [self.evidence_quality, self.reproducibility, self.utility,
                self.transferability, self.human_alignment]
        if any(d <= 0 for d in dims):
            return 0.0
        prod = 1.0
        for d in dims:
            prod *= d
        return (prod ** (1.0 / len(dims))) * (1.0 - max(0.0, min(1.0, self.risk)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "work_id": self.work_id,
            "contributor": self.contributor,
            "compute_cost": round(self.compute_cost, 6),
            "evidence_quality": round(self.evidence_quality, 6),
            "reproducibility": round(self.reproducibility, 6),
            "utility": round(self.utility, 6),
            "transferability": round(self.transferability, 6),
            "risk": round(self.risk, 6),
            "human_alignment": round(self.human_alignment, 6),
            "geometric_score": round(self.geometric_score(), 6),
            "status": self.status,
            "proofs": dict(self.proofs),
        }


# ---------------------------------------------------------------------------
# Work Contract
# ---------------------------------------------------------------------------

@dataclass
class WorkContract:
    """The 'mining block' of the useful-work network. A problem to solve,
    with evaluation criteria, budget, and risk envelope."""
    work_id: str
    dao_id: str
    problem_hash: str
    closure_target: str
    accepted_capabilities: List[str]
    evaluation: Dict[str, Any]         # e.g. {"tests_required": 42, "minimum_pass_rate": 1.0, ...}
    compute_budget: Dict[str, Any]     # e.g. {"max_input_tokens": 200000, "max_cpu_seconds": 3600, ...}
    risk: Dict[str, Any]               # e.g. {"network": "DENIED", "max_cvar": 0.05}
    reward_pool_captals_units: float
    challenge_window_seconds: int
    state: str = "OPEN"                # OPEN | LOCKED | CHALLENGED | ADJUDICATED | FINALIZED | EXPIRED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "work_id": self.work_id,
            "dao_id": self.dao_id,
            "problem_hash": self.problem_hash,
            "closure_target": self.closure_target,
            "accepted_capabilities": list(self.accepted_capabilities),
            "evaluation": dict(self.evaluation),
            "compute_budget": dict(self.compute_budget),
            "risk": dict(self.risk),
            "reward_pool_captals_units": self.reward_pool_captals_units,
            "challenge_window_seconds": self.challenge_window_seconds,
            "state": self.state,
        }


# ---------------------------------------------------------------------------
# Proof chain (PoSE, PoCT, PoTM, PoLE)
# ---------------------------------------------------------------------------

class ProofChain:
    """The four-step proof chain. Each proof is the SHA-256 of the relevant
    canonical object.

      PoSE — the rule was correctly applied?
      PoCT — the causal transition between states was valid?
      PoTM — the artifact changed nature while preserving causal identity?
      PoLE — the evolutionary trajectory remained traceable?
    """

    KINDS = ("PoSE", "PoCT", "PoTM", "PoLE")

    def __init__(self) -> None:
        self._proofs: Dict[str, Dict[str, str]] = {}

    def attach(self, work_id: str, kind: str, hash_hex: str) -> None:
        if kind not in self.KINDS:
            raise ValueError(f"unknown proof kind: {kind}")
        self._proofs.setdefault(work_id, {})[kind] = hash_hex

    def get(self, work_id: str) -> Dict[str, str]:
        return dict(self._proofs.get(work_id, {}))

    def is_complete(self, work_id: str) -> bool:
        ps = self._proofs.get(work_id, {})
        return all(k in ps for k in self.KINDS)

    def summary(self) -> Dict[str, Any]:
        n_complete = sum(1 for w in self._proofs if self.is_complete(w))
        return {
            "n_works": len(self._proofs),
            "n_complete": n_complete,
            "kinds": list(self.KINDS),
        }


# ---------------------------------------------------------------------------
# Captals Engine (M-bit calculator + reward distributor)
# ---------------------------------------------------------------------------

class CaptalsEngine:
    """The Captals engine. Computes M-bit from evidence, distributes
    simulated reward, NEVER transfers a public token.

    The reward function (proposed):

        U_i = (Q_i * R_i * T_i * V_i * E_i * H_i)^(1/6) * (1 - CVaR_i)
        W_i = U_i * D_i * A_i * P_i
        Reward_i = B_epoch * W_i / sum_j W_j

    where D=difficulty, A=admissibility, P=causal participation,
    B_epoch = epoch budget.
    """

    def __init__(self) -> None:
        self.proofs = ProofChain()
        self.mbits: List[MBit] = []

    def record(self, m: MBit) -> MBit:
        # Constitutional gate: a zero in any positive dimension => 0
        score = m.geometric_score()
        if score <= 0:
            m.status = "REJECTED"
        elif m.status == "DECLARED":
            m.status = "ADMISSIBLE_CONTRIBUTION"
        self.mbits.append(m)
        return m

    def reward(self, epoch_budget: float,
               difficulty: Dict[str, float],
               admissibility: Dict[str, float],
               participation: Dict[str, float]) -> Dict[str, float]:
        """Compute the per-MBit reward share for an epoch.

        difficulty / admissibility / participation are dicts keyed by
        work_id. If a work is missing, the default is 1.0 for difficulty
        and admissibility, 0.0 for participation (no causal contribution).
        """
        # Compute U_i for each
        u: Dict[str, float] = {}
        for m in self.mbits:
            if m.status == "REJECTED":
                continue
            u[m.work_id] = m.geometric_score()
        # Compute W_i = U_i * D_i * A_i * P_i
        w: Dict[str, float] = {}
        for wid, ui in u.items():
            d = difficulty.get(wid, 1.0)
            a = admissibility.get(wid, 1.0)
            p = participation.get(wid, 0.0)
            w[wid] = ui * d * a * p
        total_w = sum(w.values())
        out: Dict[str, float] = {}
        if total_w <= 0 or epoch_budget <= 0:
            return out
        for wid, wi in w.items():
            out[wid] = epoch_budget * (wi / total_w)
        return out

    def summary(self) -> Dict[str, Any]:
        n = len(self.mbits)
        rej = sum(1 for m in self.mbits if m.status == "REJECTED")
        return {
            "n_mbits": n,
            "n_rejected": rej,
            "n_admissible": n - rej,
            "proofs": self.proofs.summary(),
        }
