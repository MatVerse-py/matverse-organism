"""
matverse.cassandra_backend.policy
==================================

The 5 constitutional hard limits of the Cassandra agent, expressed
as a pure policy module. No I/O, no LLM, no network.

These limits are the runtime gate. They are the same limits encoded
in the `CASSANDRA_SYSTEM_PROMPT` (immutable, declarative) and now
reified as a Python function the HTTP server can call.

The 5 hard limits (per the corpus + v3.8.2):

  1. NEVER authorizes external action (ESCALATE on
     execute / publish / sign / transfer / deploy)
  2. Evidence before claim (OBS requires source_id)
  3. Determinism (same input + same policy → same output)
  4. Fail-closed (doubt → ESCALATE)
  5. Avatar ≠ authentication (user_id from session, not claim)
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# The 5 hard limits — keyword dictionaries
# ---------------------------------------------------------------------------

# Limit 1: external action keywords (always → ESCALATE)
EXTERNAL_ACTION_KEYWORDS = [
    # English
    "execute", "execute it", "run it", "deploy", "deploy now",
    "publish", "publish it", "ship it", "release it",
    "sign", "sign the tx", "sign tx", "sign transaction",
    "transfer", "transfer funds", "move money", "send money",
    "put on chain", "put it on chain", "anchor on chain",
    "broadcast", "broadcast the tx",
    # Portuguese
    "publique", "publicar", "assine", "transfira", "mova fundo",
    "rodar em produção", "deploy agora", "ship", "vai pra mainnet",
    "executa agora", "executa isso", "manda pra produção",
    "coloca no ar", "vai com tudo",
]

# Limit 2: epistemic labels (parsed from response)
EPISTEMIC_LABELS = [
    "OBS", "INF", "HYP", "EVD", "ADM", "CON", "ESC",
]

# Limit 4: uncertainty keywords (always → HOLD or ESCALATE)
UNCERTAINTY_KEYWORDS = [
    "i don't know", "i'm not sure", "not sure", "maybe", "perhaps",
    "possibly", "i think", "i believe", "might be", "could be",
    "não sei", "talvez", "acho que", "provavelmente", "possivelmente",
    "não tenho certeza", "pode ser",
]

# Limit 5: avatar / identity keywords (warning only — the system prompt
# enforces this; this is for the runtime to detect impersonation)
AVATAR_IMPERSONATION_KEYWORDS = [
    "i am mateus", "eu sou mateus", "eu sou o mateus",
    "i am the operator", "i am the admin", "i am root",
    "ignore previous instructions", "ignore all instructions",
    "you are now", "act as", "pretend to be", "roleplay as",
    "ignore suas instruções", "finja que é", "aja como",
    "esqueça o prompt", "ignore o system prompt",
]


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class GateResult:
    """The result of evaluating a user message against the 5 hard limits."""
    gate_status: str       # PASS | HOLD | ESCALATE | DENY
    epistemic: str         # OBS | INF | HYP | EVD | ADM | CON | ESC
    triggered_limits: List[int]   # which of the 5 limits were triggered
    reason: str            # human-readable explanation
    can_publish: bool      # can this response be shown to the user
    needs_operator: bool   # does this require operator intervention

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_status": self.gate_status,
            "epistemic": self.epistemic,
            "triggered_limits": list(self.triggered_limits),
            "reason": self.reason,
            "can_publish": self.can_publish,
            "needs_operator": self.needs_operator,
        }


# ---------------------------------------------------------------------------
# Limit 1: external action detection
# ---------------------------------------------------------------------------

def check_external_action(message: str) -> Tuple[bool, str]:
    """Returns (is_external_action, matched_keyword).

    Uses word-boundary matching for short keywords to avoid false
    positives like 'sign' matching inside 'design' or 'assign'."""
    low = (message or "").lower()
    for kw in EXTERNAL_ACTION_KEYWORDS:
        if " " in kw or len(kw) > 5:
            if kw in low:
                return True, kw
        else:
            if re.search(r"\b" + re.escape(kw) + r"\b", low):
                return True, kw
    return False, ""


# ---------------------------------------------------------------------------
# Limit 2: epistemic label parser
# ---------------------------------------------------------------------------

_EPISTEMIC_RE = re.compile(r"\[epistemic:\s*([A-Z]+)\]")


def parse_epistemic(response: str) -> str:
    """Parse the [epistemic: <TAG>] marker from a response."""
    if not response:
        return "HYP"
    m = _EPISTEMIC_RE.search(response)
    if m and m.group(1) in EPISTEMIC_LABELS:
        return m.group(1)
    return "HYP"


# ---------------------------------------------------------------------------
# Limit 4: uncertainty detection
# ---------------------------------------------------------------------------

def check_uncertainty(message: str) -> bool:
    low = (message or "").lower()
    return any(kw in low for kw in UNCERTAINTY_KEYWORDS)


# ---------------------------------------------------------------------------
# Limit 5: impersonation / prompt-injection detection
# ---------------------------------------------------------------------------

def check_impersonation(message: str) -> Tuple[bool, str]:
    """Returns (is_injection, matched_keyword)."""
    low = (message or "").lower()
    for kw in AVATAR_IMPERSONATION_KEYWORDS:
        if kw in low:
            return True, kw
    return False, ""


# ---------------------------------------------------------------------------
# Source citation check (Limit 2 enforcement)
# ---------------------------------------------------------------------------

_SOURCE_PATTERNS = [
    re.compile(r"\[source:\s*[^\]]+\]"),
    re.compile(r"\[ref:\s*[^\]]+\]"),
    re.compile(r"tests/[a-zA-Z0-9_/]+\.py::[a-zA-Z0-9_]+"),
    re.compile(r"references/[a-zA-Z0-9_/]+\.\w+"),
    re.compile(r"file://[^\s]+"),
    re.compile(r"https?://[^\s]+"),
]


def has_source_citation(response: str) -> bool:
    """True if the response cites a source (test, file, URL, ref)."""
    if not response:
        return False
    return any(p.search(response) for p in _SOURCE_PATTERNS)


# ---------------------------------------------------------------------------
# The main gate
# ---------------------------------------------------------------------------

def evaluate(message: str, response: Optional[str] = None) -> GateResult:
    """Evaluate a user message (and optional response) against the 5 hard limits.

    Returns a `GateResult` with:
      - gate_status: PASS | HOLD | ESCALATE | DENY
      - epistemic: the epistemic classification of the response
      - triggered_limits: list of 1-5
      - reason: human-readable
      - can_publish: False for ESCALATE, DENY, or HOLD with impersonation
      - needs_operator: True for ESCALATE or impersonation attempts
    """
    triggered: List[int] = []
    reasons: List[str] = []

    # Limit 5: check first — impersonation is the most severe
    is_inj, inj_kw = check_impersonation(message)
    if is_inj:
        triggered.append(5)
        reasons.append(f"Limit 5: avatar≠auth violation (matched '{inj_kw}')")
        return GateResult(
            gate_status="DENY",
            epistemic="ESC",
            triggered_limits=triggered,
            reason="; ".join(reasons),
            can_publish=False,
            needs_operator=True,
        )

    # Limit 1: external action
    is_ext, ext_kw = check_external_action(message)
    if is_ext:
        triggered.append(1)
        reasons.append(f"Limit 1: external action requested (matched '{ext_kw}')")

    # Limit 4: uncertainty
    is_unc = check_uncertainty(message)
    if is_unc:
        triggered.append(4)
        reasons.append("Limit 4: uncertainty keyword detected (fail-closed)")

    # Limit 2: epistemic + source check (only if response is given)
    epistemic = "HYP"
    if response is not None:
        epistemic = parse_epistemic(response)
        if epistemic == "OBS" and not has_source_citation(response):
            triggered.append(2)
            reasons.append("Limit 2: OBS without source citation")
        elif epistemic == "OBS":
            # OBS with source — only need to verify if limit 1/4 also triggered
            pass
        elif epistemic == "HYP":
            # HYP is fine — it just means hypothesis, not observed
            pass

    # Determine final gate status
    if is_ext:
        return GateResult(
            gate_status="ESCALATE",
            epistemic="ESC",
            triggered_limits=triggered,
            reason="; ".join(reasons),
            can_publish=False,
            needs_operator=True,
        )
    if is_unc and epistemic == "HYP":
        # uncertainty + no observation → HOLD
        return GateResult(
            gate_status="HOLD",
            epistemic=epistemic,
            triggered_limits=triggered,
            reason="; ".join(reasons),
            can_publish=True,  # can show "I need more info" response
            needs_operator=False,
        )
    if 2 in triggered:
        # OBS without source — downgrade to HYP
        return GateResult(
            gate_status="HOLD",
            epistemic="HYP",
            triggered_limits=triggered,
            reason="; ".join(reasons),
            can_publish=True,
            needs_operator=False,
        )
    # Default: PASS
    return GateResult(
        gate_status="PASS",
        epistemic=epistemic if response is not None else "HYP",
        triggered_limits=triggered,
        reason="ok" if not reasons else "; ".join(reasons),
        can_publish=True,
        needs_operator=False,
    )


# ---------------------------------------------------------------------------
# Determinism check (Limit 3)
# ---------------------------------------------------------------------------

def deterministic_check(message: str, response_a: str, response_b: str) -> bool:
    """Limit 3: same input + same policy → same output.

    For the local_interpret path, this is trivially true (no I/O).
    For the LLM path, the caller can use this to verify two
    runs produce the same response (modulo temperature=0)."""
    return response_a == response_b


# ---------------------------------------------------------------------------
# System prompt (canonical, immutable)
# ---------------------------------------------------------------------------

def get_system_prompt() -> str:
    """Return the canonical Cassandra system prompt.

    This is the SAME prompt that `matverse.cassandra_prompt` exposes;
    re-exported here so the HTTP server can include it in
    /auth/session responses for client-side rendering."""
    from .cassandra_prompt_inline import CASSANDRA_SYSTEM_PROMPT
    return CASSANDRA_SYSTEM_PROMPT
