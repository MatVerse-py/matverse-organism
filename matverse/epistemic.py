"""
matverse.epistemic
==================

Epistemic state machine and belief-combination algebra.

Implements the v0.2 kernel corrections:

1. EpistemicState (8 states including ESCALATE for conflict preservation)
2. Dempster-Shafer combination with conflict preservation
3. Dung preferred extensions for argumentation
4. IRC (Índice de Resolução Cognitiva) = 1 − entropy / log(2)

These are 13th–15th constitutional organs in the v3.8.0 model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Epistemic states
# ---------------------------------------------------------------------------

class EpistemicState(str, Enum):
    NULL      = "Ø"     # Unresolved
    OBS       = "OBS"   # Observed
    INF       = "INF"   # Inferred
    HYP       = "HYP"   # Live hypothesis
    EVD       = "EVD"   # Sustained by evidence
    ADM       = "ADM"   # Admissible
    CON       = "CON"   # Consolidated
    ESCALATE  = "ESC"   # Conflict detected (CORREÇÃO 2)


# ---------------------------------------------------------------------------
# Policy (versioned)
# ---------------------------------------------------------------------------

@dataclass
class EpistemicPolicy:
    """A versioned decision policy for a domain."""
    id: str
    version: str
    domain: str
    entropy_max: float = 0.3
    null_max: float = 0.2
    irc_min: float = 0.7
    work_cap: float = 10.0
    conflict_threshold: float = 0.8
    projection_penalty: float = 2.0
    social_pressure_weight: float = 0.3


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

@dataclass
class SourceMetadata:
    source_type: str  # 'observation' | 'inference' | 'projection'
    independence_score: float  # 0..1
    justification: str = ""


@dataclass
class Evidence:
    id: str
    content: object
    metadata: SourceMetadata
    hypothesis_id: str
    strength: float  # 0..1


# ---------------------------------------------------------------------------
# Belief record
# ---------------------------------------------------------------------------

@dataclass
class BeliefRecord:
    """Tracks the belief, uncertainty, and work of a hypothesis."""
    id: str
    state: EpistemicState = EpistemicState.HYP
    belief: float = 0.5
    uncertainty: float = 0.5
    work_spent: float = 0.0
    evidence_ids: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Dempster-Shafer with conflict preservation
# ---------------------------------------------------------------------------

def dempster_combine(evidences: List[Evidence],
                     policy: EpistemicPolicy
                     ) -> Tuple[float, float, float, EpistemicState]:
    """Combine `evidences` (each with strength) into (belief, uncertainty, conflict, state).

    Conflict is preserved, not normalized away. If conflict > policy.conflict_threshold,
    the state is ESCALATE.
    """
    if not evidences:
        return 0.5, 0.5, 0.0, EpistemicState.NULL

    belief = 0.0
    uncertainty = 1.0
    for ev in evidences:
        m_belief = max(0.0, min(1.0, ev.strength))
        m_uncertainty = 1.0 - m_belief
        new_conflict = belief * m_uncertainty + uncertainty * (1.0 - m_belief)
        if new_conflict > policy.conflict_threshold:
            return 0.0, 1.0, 1.0, EpistemicState.ESCALATE
        denom = 1.0 - new_conflict
        if denom <= 1e-12:
            return 0.0, 1.0, 1.0, EpistemicState.ESCALATE
        new_belief = (belief * m_belief + uncertainty * m_belief) / denom
        new_uncertainty = (uncertainty * m_uncertainty) / denom
        belief = min(1.0, new_belief)
        uncertainty = min(1.0, new_uncertainty)

    belief = max(0.0, min(1.0, belief))
    uncertainty = max(0.0, min(1.0, uncertainty))
    return belief, uncertainty, 0.0, _decide_state(belief, uncertainty, policy)


def _decide_state(belief: float, uncertainty: float, policy: EpistemicPolicy
                  ) -> EpistemicState:
    """Decide the epistemic state from belief, uncertainty, and the policy."""
    if belief >= 0.95 and uncertainty < policy.null_max:
        return EpistemicState.CON
    if belief >= 0.8 and uncertainty < policy.null_max * 1.5:
        return EpistemicState.ADM
    if belief >= 0.5:
        return EpistemicState.EVD
    if belief >= 0.2:
        return EpistemicState.HYP
    if belief > 0.0:
        return EpistemicState.INF
    return EpistemicState.NULL


# ---------------------------------------------------------------------------
# IRC (Índice de Resolução Cognitiva)
# ---------------------------------------------------------------------------

def irc(belief: float, uncertainty: float) -> float:
    """IRC = 1 − entropy / log(2), clamped to [0, 1].

    Entropy is the binary entropy H(p) = -p log p - (1-p) log(1-p).
    For belief=1.0 or belief=0.0 the entropy is exactly 0.
    """
    if belief >= 1.0:
        return 1.0
    if belief <= 0.0:
        return 0.0
    p = max(1e-12, min(1.0 - 1e-12, belief))
    q = 1.0 - p
    H = -p * math.log(p) - q * math.log(q)
    return max(0.0, min(1.0, 1.0 - H / math.log(2)))


# ---------------------------------------------------------------------------
# Dung preferred extensions
# ---------------------------------------------------------------------------

def attack_graph(records: Dict[str, BeliefRecord],
                 evidences: Dict[str, Evidence],
                 policy: EpistemicPolicy
                 ) -> Dict[str, Set[str]]:
    """Build the attack graph: h1 attacks h2 if their evidence similarity is low.

    Conflict(h1, h2) = 1 − |E1 ∩ E2| / |E1 ∪ E2|  (Jaccard distance).
    If conflict > conflict_threshold, mutual attack (we keep it symmetric).
    """
    attacks: Dict[str, Set[str]] = {h: set() for h in records}
    ids = list(records.keys())
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            E_a = set(records[a].evidence_ids)
            E_b = set(records[b].evidence_ids)
            if not E_a and not E_b:
                continue
            union = E_a | E_b
            if not union:
                continue
            jaccard = len(E_a & E_b) / len(union)
            conflict = 1.0 - jaccard
            if conflict > policy.conflict_threshold:
                attacks[a].add(b)
                attacks[b].add(a)
    return attacks


def _is_admissible(subset: Set[str], attacks: Dict[str, Set[str]]) -> bool:
    """Dung admissibility: subset is conflict-free and self-defending.

    1. Conflict-free: no a, b in S with a attacks b.
    2. Self-defending: every a in S has its external attackers
       counter-attacked by some member of S.
    """
    # 1. Conflict-free
    for a in subset:
        for b in subset:
            if a != b and b in attacks.get(a, set()):
                return False
    # 2. Self-defending
    for a in subset:
        for attacker in attacks.get(a, set()):
            if attacker not in subset:
                defenders = {b for b in subset if attacker in attacks.get(b, set())}
                if not defenders:
                    return False
    return True


def dung_preferred_extensions(records: Dict[str, BeliefRecord],
                              evidences: Dict[str, Evidence],
                              policy: EpistemicPolicy) -> List[Set[str]]:
    """Return all preferred extensions (maximal admissible subsets)."""
    ids = list(records.keys())
    attacks = attack_graph(records, evidences, policy)
    # Enumerate all non-empty subsets and check admissibility (n small)
    admissible: List[Set[str]] = []
    n = len(ids)
    for mask in range(1, 1 << n):
        subset = {ids[k] for k in range(n) if (mask >> k) & 1}
        if _is_admissible(subset, attacks):
            admissible.append(subset)
    # Preferred = maximal by inclusion
    preferred: List[Set[str]] = []
    for s in admissible:
        is_max = True
        for t in admissible:
            if s != t and s < t:
                is_max = False
                break
        if is_max:
            preferred.append(s)
    return preferred


# ---------------------------------------------------------------------------
# Ω-Gate evaluation
# ---------------------------------------------------------------------------

@dataclass
class GateDecision:
    decision: str  # ADMISSIBLE | HOLD | ESCALATE | REJECT
    state: EpistemicState
    reason: str
    belief: float
    uncertainty: float
    conflict: float
    entropy: float
    irc_value: float
    work_spent: float


def evaluate_gate(record: BeliefRecord,
                  evidences: List[Evidence],
                  policy: EpistemicPolicy) -> GateDecision:
    """Ω-Gate: full evaluation with conflict preservation."""
    belief, uncertainty, conflict, state = dempster_combine(evidences, policy)
    # Binary entropy for the IRC denominator
    p = max(1e-12, min(1.0 - 1e-12, belief))
    H = -p * math.log(p) - (1 - p) * math.log(1 - p)
    irc_value = max(0.0, min(1.0, 1.0 - H / math.log(2)))

    if state == EpistemicState.ESCALATE:
        return GateDecision(
            decision="ESCALATE",
            state=state,
            reason=f"Conflict detected (K={conflict:.3f} > {policy.conflict_threshold:.3f})",
            belief=belief, uncertainty=uncertainty, conflict=conflict,
            entropy=H, irc_value=irc_value, work_spent=record.work_spent,
        )

    meets = (record.work_spent >= policy.work_cap * 0.5
             and H <= policy.entropy_max
             and uncertainty <= policy.null_max
             and irc_value >= policy.irc_min
             and conflict < policy.conflict_threshold)

    if meets:
        return GateDecision(
            decision="ADMISSIBLE",
            state=EpistemicState.ADM,
            reason="All policy criteria met",
            belief=belief, uncertainty=uncertainty, conflict=conflict,
            entropy=H, irc_value=irc_value, work_spent=record.work_spent,
        )

    reasons = []
    if record.work_spent < policy.work_cap * 0.5:
        reasons.append(f"insufficient work ({record.work_spent:.2f})")
    if H > policy.entropy_max:
        reasons.append(f"high entropy ({H:.3f})")
    if uncertainty > policy.null_max:
        reasons.append(f"high uncertainty ({uncertainty:.3f})")
    if irc_value < policy.irc_min:
        reasons.append(f"low IRC ({irc_value:.3f})")
    return GateDecision(
        decision="HOLD",
        state=EpistemicState.HYP,
        reason="; ".join(reasons),
        belief=belief, uncertainty=uncertainty, conflict=conflict,
        entropy=H, irc_value=irc_value, work_spent=record.work_spent,
    )
