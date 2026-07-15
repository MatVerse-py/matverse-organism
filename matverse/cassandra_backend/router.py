"""
matverse.cassandra_backend.router
==================================

The LLM router for Cassandra: ZERO / TINY / BURST.

Per the corpus and the previous Base44 chat, Cassandra's response
strategy is:
  - ZERO  : no LLM, deterministic local_interpret (always works)
  - TINY  : small local model (Phi, Qwen, Gemma) — optional
  - BURST : large remote model (NVIDIA NIM, etc.) — requires
             explicit operator authorization and capability token

The router is fail-closed: if BURST is requested but not authorized,
it falls back to TINY (or ZERO if no TINY model is configured).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

# Default app id (Base44 MatVerse URANO OSX). Kept here for
# diagnostic purposes only; this is the app the backend would
# talk to, not the app the user is building in Base44.
DEFAULT_APP_ID = "6a2dd76b300afd3eb43293d7"
# The Cassandra/Superagent ID in Base44 (the one the Base44 app
# is meant to integrate with). This is informational; the backend
# itself does not call Base44 (it IS the backend).
SUPERAGENT_ID = "6a3f8dcd43af4cd136e09be2"


@dataclass
class RouteDecision:
    """The router's decision for a given message."""
    route: str                       # ZERO | TINY | BURST
    reason: str                      # why this route was chosen
    requires_operator: bool          # does this require operator approval
    escalation_keyword: str = ""     # the keyword that triggered escalation (if any)
    model_hint: str = ""             # suggested model id (for TINY/BURST)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "route": self.route,
            "reason": self.reason,
            "requires_operator": self.requires_operator,
            "escalation_keyword": self.escalation_keyword,
            "model_hint": self.model_hint,
        }


# ---------------------------------------------------------------------------
# External-action detection (duplicated from policy for module isolation)
# ---------------------------------------------------------------------------

EXTERNAL_KEYWORDS = [
    "execute", "deploy", "publish", "sign", "transfer", "ship",
    "put on chain", "broadcast", "anchor",
    "publique", "publicar", "assine", "transfira", "mova fundo",
    "rodar em produção", "deploy agora", "vai pra mainnet",
    "executa agora", "manda pra produção", "coloca no ar",
]


def _has_external_keyword(message: str) -> str:
    import re as _re
    low = (message or "").lower()
    for kw in EXTERNAL_KEYWORDS:
        # Word-boundary match for short keywords to avoid false positives
        # like "sign" matching inside "design" or "assign".
        if " " in kw or len(kw) > 5:
            if kw in low:
                return kw
        else:
            if _re.search(r"\b" + _re.escape(kw) + r"\b", low):
                return kw
    return ""


# ---------------------------------------------------------------------------
# Heuristic complexity score (0..1) — used to pick ZERO vs TINY
# ---------------------------------------------------------------------------

_COMPLEX_SIGNALS = [
    r"\b(crie|criar|build|implement|generate)\b",
    r"\b(explique|explain|descreva|describe)\b",
    r"\b(compare|analyse|analise|analyze)\b",
    r"\b(refactor|rewrite|reescreva)\b",
    r"\b(design|architect|arquitete|projete)\b",
    r"\?$",  # ends with question mark
    r"^\s*\d+\.\s",  # numbered list
]


def complexity_score(message: str) -> float:
    """Return a 0..1 score of how complex the request is.

    Heuristic: count complex-signal regex matches, normalize by length."""
    if not message:
        return 0.0
    low = message.lower()
    hits = sum(1 for p in _COMPLEX_SIGNALS if re.search(p, low))
    # normalize: 0 hits → 0.0, 5+ hits → 1.0
    return min(1.0, hits / 5.0)


# ---------------------------------------------------------------------------
# The main router
# ---------------------------------------------------------------------------

def route(message: str, prefer_burst: bool = False,
          burst_authorized: bool = False) -> RouteDecision:
    """Decide which route to use for a given message.

    Args:
      message: the user's message
      prefer_burst: the client prefers BURST (e.g., user asked for "deep
                     analysis"). Only honored if burst_authorized=True.
      burst_authorized: operator has explicitly authorized BURST for
                        this request (capability token verified).

    Returns:
      RouteDecision with route, reason, requires_operator.
    """
    if not message:
        return RouteDecision(
            route="ZERO",
            reason="empty message",
            requires_operator=False,
            model_hint="local_interpret",
        )

    # Step 1: external action always routes to ZERO with ESCALATE flag
    ext_kw = _has_external_keyword(message)
    if ext_kw:
        return RouteDecision(
            route="ZERO",
            reason=f"external action detected ('{ext_kw}'); fail-closed, no LLM",
            requires_operator=True,
            escalation_keyword=ext_kw,
            model_hint="local_interpret",
        )

    # Step 2: BURST path (only if authorized)
    if prefer_burst and burst_authorized:
        return RouteDecision(
            route="BURST",
            reason="operator authorized BURST; using large remote model",
            requires_operator=False,
            model_hint="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        )

    # Step 3: TINY path (if configured and complexity is high)
    complexity = complexity_score(message)
    has_tiny = bool(os.environ.get("CASSANDRA_TINY_MODEL"))  # e.g., "phi", "qwen"
    if complexity >= 0.6 and has_tiny:
        return RouteDecision(
            route="TINY",
            reason=f"complexity={complexity:.2f} ≥ 0.6; TINY model available",
            requires_operator=False,
            model_hint=os.environ.get("CASSANDRA_TINY_MODEL", "phi-3-mini"),
        )

    # Step 4: default ZERO (deterministic, no LLM, no network)
    return RouteDecision(
        route="ZERO",
        reason=f"complexity={complexity:.2f} < 0.6 or no TINY; deterministic local",
        requires_operator=False,
        model_hint="local_interpret",
    )


# ---------------------------------------------------------------------------
# Local interpreter (the ZERO route)
# ---------------------------------------------------------------------------

def local_interpret(message: str) -> str:
    """Deterministic interpretation of a user message. No LLM.

    Returns a Cassandra-style response:
      - short classification of the request
      - relevant constitutional references
      - suggestion (if any) or escalation (if external action)
    """
    msg = (message or "").strip()
    low = msg.lower()
    parts = []

    # 1. external-action check (always fail-closed)
    ext_kw = _has_external_keyword(message)
    if ext_kw:
        return (
            "Esta ação está fora do escopo de Cassandra. "
            "Requer Ω-Gate + EvidenceOS + operador humano. "
            "Posso PREPARAR a proposta. A decisão é de Ω-Gate + você.\n"
            f"[epistemic: ESC] Pedido de ação externa detectado: '{ext_kw}'."
        )

    # 2. introspection
    if "o que é" in low or "explique" in low or "explain" in low:
        parts.append("Interpretação: pedido de explicação.")
        if "omega" in low or "ω" in low:
            parts.append(
                "Ω-Score canônica (do corpus v3.6): Ω ≈ 0.81, "
                "calculada por omega_score(c_inv=0.92, pbr=21.91, "
                "r_rec=4.0, a_aut=0.78, f_ant=0.85), todas as dims "
                "normalizadas em [0,1]. [epistemic: OBS] ver "
                "tests/test_omega.py::test_canonical_closure_v36."
            )
        elif "mnb" in low or "mem-nano" in low or "5-tuple" in low:
            parts.append(
                "MNB 5-tuple: m = (e, Ψ, C, τ, h) com ρ = Ψ·τ/C. "
                "MNB é camada POSTERIOR na linhagem canônica "
                "(Captals×Gate → PoSE+ledger → Cassandra → MNB → "
                "M-Bit → Paper-Contract). [epistemic: OBS] ver "
                "references/lineage.md."
            )
        elif "captals" in low:
            parts.append(
                "Captals: a gênese econômica (Captals × Gate). "
                "MNB é camada posterior. M-Bit é garantia de "
                "avanço. Não são substituições. [epistemic: OBS] "
                "ver references/lineage.md § Os sete layers."
            )
        elif "cassandra" in low:
            parts.append(
                "Cassandra = modelo informacional (não persona). "
                "Time de 7 skills: interpreter, grounding, TACE, "
                "H-Axis, Ω-Gate, ledger, impact_briefing. v3.8.0 "
                "implementa 4 de 7; 3 HOLD. [epistemic: OBS] ver "
                "references/cassandra_model.md."
            )
        elif "cog" in low or "cortex" in low or "metacortex" in low:
            parts.append(
                "COG (Cognitive Operational Grid) = a defesa "
                "principal do MatVerse. Córtex gera, Exocórtex "
                "externaliza, Metacórtex reflete. COG deu trilha "
                "para o pensamento. [epistemic: OBS] ver "
                "matverse/canonical.py (12 órgãos)."
            )
        else:
            parts.append(
                "Pedido genérico de explicação. Sem claim OBS, "
                "marco como HYP. [epistemic: HYP] traga evidência "
                "executável (test, log, receipt) para eu classificar."
            )
    # 3. routing
    elif "rode" in low or "run" in low:
        parts.append(
            "Interpretação: pedido de execução. Em v3.8.2 isso "
            "rota para URANO. URANO está PROTOTYPE no organismo; "
            "a execução local está HOLD. [epistemic: HYP] aguarde "
            "P3 (Shadow Evaluator) para execução real."
        )
    elif "crie" in low or "criar" in low or "nova" in low:
        parts.append(
            "Interpretação: pedido de criação. Em v3.8.2 isso "
            "rota para COG (Campo de Hipóteses). Posso PREPARAR "
            "a hipótese, você REVISA, e então o Ω-Gate decide. "
            "[epistemic: HYP] hipótese precisa de evidência para "
            "virar ADM."
        )
    else:
        parts.append(
            "Interpretação: pedido geral. Para roteamento preciso, "
            "use verbos canônicos: 'crie', 'rode', 'explique', "
            "'valide', 'publique', 'execute'. O verbo 'publique' "
            "ou 'execute' aciona fail-closed (ESCALATE). "
            "[epistemic: HYP] sem claim observável no input."
        )

    parts.append(
        "[epistemic: HYP→OBS upgradeável] Se você trazer "
        "evidência executável (test, log, receipt), eu reclassifico."
    )
    return "\n".join(parts)
