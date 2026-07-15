"""
matverse.cassandra_base44
==========================

Base44 client + agent integration for the Cassandra conversational
agent. Two modes:

  - STANDALONE   : no Base44, runs locally with the constitutional
                    system prompt and the corpus. No LLM required;
                    uses the deterministic rule-based interpreter.

  - BASE44_REMOTE: connects to a Base44 app (default app id is
                    '6a2dd76b300afd3eb43293d7' / 'MatVerse URANO OSX')
                    and uses the Base44 agent API to converse.

  - HYBRID       : uses Base44 as a storage backend (entities:
                    RuntimeIntent, RuntimeReceipt, CassandraRun)
                    and a local interpreter for responses.

Constitutional position: Cassandra prepares, the operator signs,
the world witnesses. This module never signs or publishes — it only
sends, reads, and logs.

The Base44 API key is read from the environment variable
`BASE44_API_KEY` and is never stored on disk. If the variable is
absent, the module falls back to STANDALONE mode automatically.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


DEFAULT_APP_ID = "6a2dd76b300afd3eb43293d7"
DEFAULT_BASE_URL = "https://api.base44.com/v1"
API_KEY_ENV = "BASE44_API_KEY"

# The default Base44 agent id for the OSX chat is hard-coded here.
# The user can override via the `agent_id` parameter to Base44Agent.
DEFAULT_OSX_CHAT_AGENT = "osx_chat"


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class Base44Error(RuntimeError):
    """Raised on any Base44 API error."""

class Base44Client:
    """Thin REST client for the Base44 public API.

    Endpoints used (per the Base44 docs page in the corpus):
      GET  /entities/{name}                    — list records
      POST /entities/{name}                    — create record
      GET  /entities/{name}/{id}               — get record
      PUT  /entities/{name}/{id}               — update record
      GET  /apps/{id}/agents/conversations     — list conversations
      POST /apps/{id}/agents/conversations     — create conversation
      GET  /apps/{id}/agents/conversations/{cid}  — get conversation
      POST /apps/{id}/agents/conversations/{cid}/messages — send message
    """

    def __init__(self, api_key: Optional[str] = None,
                 base_url: str = DEFAULT_BASE_URL,
                 app_id: str = DEFAULT_APP_ID) -> None:
        self.api_key = api_key or os.environ.get(API_KEY_ENV, "")
        self.base_url = base_url.rstrip("/")
        self.app_id = app_id
        if not self.api_key:
            # don't raise — caller may be using STANDALONE mode
            pass

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _request(self, method: str, path: str,
                body: Optional[Dict[str, Any]] = None,
                params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.is_configured:
            raise Base44Error("BASE44_API_KEY not set")
        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, method=method,
            headers={
                "api_key": self.api_key,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = resp.read().decode("utf-8")
                return json.loads(payload) if payload else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise Base44Error(f"HTTP {e.code}: {body}") from e
        except urllib.error.URLError as e:
            raise Base44Error(f"URL error: {e}") from e

    # ---- entities ----
    def list_entities(self, entity: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self._request("GET", f"/entities/{entity}", params={"limit": limit})

    def get_entity(self, entity: str, record_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/entities/{entity}/{record_id}")

    def create_entity(self, entity: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", f"/entities/{entity}", body=fields)

    # ---- agent conversations ----
    def list_conversations(self) -> List[Dict[str, Any]]:
        return self._request("GET", f"/apps/{self.app_id}/agents/conversations")

    def create_conversation(self, title: str = "cassandra-session") -> Dict[str, Any]:
        return self._request("POST", f"/apps/{self.app_id}/agents/conversations",
                              body={"title": title})

    def send_message(self, conversation_id: str, content: str) -> Dict[str, Any]:
        return self._request("POST",
            f"/apps/{self.app_id}/agents/conversations/{conversation_id}/messages",
            body={"role": "user", "content": content})


# ---------------------------------------------------------------------------
# Local interpreter (no LLM, deterministic)
# ---------------------------------------------------------------------------

def local_interpret(message: str, corpus_hits: List[str] = None) -> str:
    """Deterministic interpretation of a user message. No LLM.

    Returns a Cassandra-style response:
      - short classification of the request
      - relevant constitutional references
      - suggestion (if any) or escalation (if external action)
    """
    if corpus_hits is None:
        corpus_hits = []
    msg = (message or "").strip()
    low = msg.lower()
    parts = []

    # 1. external-action check (always fail-closed)
    action_keywords = [
        "execute", "rodar em produção", "publique", "publicar",
        "assine", "transfira", "mova fundo", "deploy agora",
        "ship it", "put on chain", "sign tx",
    ]
    if any(k in low for k in action_keywords):
        return (
            "Esta ação está fora do escopo de Cassandra. "
            "Requer Ω-Gate + EvidenceOS + operador humano. "
            "Posso PREPARAR a proposta. A decisão é de Ω-Gate + você.\n"
            "[epistemic: ESC] Pedido de ação externa detectado."
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
        elif "mnb" in low or "mem-nano" in low or "5-tuple" in low or "5-tuple" in low:
            parts.append(
                "MNB 5-tuple: m = (e, Ψ, C, τ, h) com ρ = Ψ·τ/C. "
                "MNB é camada POSTERIOR na linhagem canônica "
                "(Captals×Gate → PoSE+ledger → Cassandra → MNB → "
                "M-Bit → Paper-Contract). [epistemic: OBS] ver "
                "references/lineage.md."
            )
        elif "gthdl" in low or "hamiltoniano" in low:
            parts.append(
                "GTHDL: dρ/dt = -i[Ĥ_Σ, ρ] com Ĥ_Σ = λ_Ω·Ω̂ + "
                "λ_Ψ·Ψ̂ + λ_C·Ĉ + λ_T·T̂. v3.8.0 implementa via "
                "Taylor expansion (válido para dt curto). "
                "[epistemic: OBS] ver matverse/hamiltonian.py."
            )
        elif "riemann" in low or "manifold" in low or "manifolde" in low:
            parts.append(
                "Riemannian Memory Manifold: M = (O, R, g, Φ, ρ). "
                "v3.8.0 usa tensor 4-tensor esparso (stdlib only). "
                "[epistemic: OBS] ver matverse/riemannian.py."
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

    if corpus_hits:
        parts.append("Hits no corpus local:")
        for h in corpus_hits[:3]:
            parts.append(f"  - {h[:120]}")

    parts.append(
        "[epistemic: HYP→OBS upgradeável] Se você trazer "
        "evidência executável (test, log, receipt), eu reclassifico."
    )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Agent wrapper
# ---------------------------------------------------------------------------

@dataclass
class CassandraRun:
    """A single Cassandra conversation run. Mirrors the Base44
    `CassandraRun` entity (referenced in the corpus)."""
    run_id: str
    conversation_id: str
    user_message: str
    cassandra_response: str
    epistemic_classification: str
    gate_status: str  # PASS | HOLD | ESCALATE | DENY
    created_at: int
    used_base44: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "conversation_id": self.conversation_id,
            "user_message": self.user_message,
            "cassandra_response": self.cassandra_response,
            "epistemic_classification": self.epistemic_classification,
            "gate_status": self.gate_status,
            "created_at": self.created_at,
            "used_base44": self.used_base44,
            "metadata": dict(self.metadata),
        }


class CassandraAgent:
    """The Cassandra agent. Two modes: STANDALONE (no LLM, no Base44)
    and BASE44_REMOTE (uses Base44 chat API). Always constitutional.
    """

    def __init__(self,
                 base44: Optional[Base44Client] = None,
                 mode: str = "auto",
                 system_prompt: Optional[str] = None) -> None:
        self.base44 = base44 or Base44Client()
        if mode == "auto":
            self.mode = "base44" if self.base44.is_configured else "standalone"
        else:
            self.mode = mode
        # lazy import to avoid hard dep
        from .cassandra_prompt import CASSANDRA_SYSTEM_PROMPT
        self.system_prompt = system_prompt or CASSANDRA_SYSTEM_PROMPT
        self.runs: List[CassandraRun] = []

    @property
    def is_base44(self) -> bool:
        return self.mode == "base44"

    def _new_run_id(self) -> str:
        return f"cassandra-run-{int(time.time() * 1_000_000)}"

    def _classify_gate(self, response: str) -> str:
        low = response.lower()
        if "escalone" in low or "esc" in low or "fora do escopo" in low:
            return "ESCALATE"
        if "deny" in low or "recus" in low or "interditad" in low:
            return "DENY"
        if "hold" in low:
            return "HOLD"
        return "PASS"

    def _classify_epistemic(self, response: str) -> str:
        # Find the [epistemic: <TAG>] marker
        import re
        m = re.search(r"\[epistemic:\s*([A-Z]+)\]", response)
        if m:
            return m.group(1)
        return "HYP"

    def chat(self, user_message: str,
             conversation_id: Optional[str] = None,
             persist: bool = False) -> CassandraRun:
        """Send a message and get a Cassandra response.

        - STANDALONE: uses local_interpret()
        - BASE44_REMOTE: uses Base44 chat API
        - persist=True: writes a CassandraRun to Base44 (if configured)
        """
        run_id = self._new_run_id()
        ts = int(time.time())

        if self.is_base44:
            try:
                if not conversation_id:
                    conv = self.base44.create_conversation("cassandra-session")
                    conversation_id = conv.get("id", "unknown")
                resp = self.base44.send_message(conversation_id, user_message)
                response_text = resp.get("content") or resp.get("text") or str(resp)
                used = True
            except Base44Error as e:
                # fail-open to local so the user still gets a constitutional response
                response_text = (
                    f"[FALLBACK local — Base44 indisponível: {e}]\n\n"
                    + local_interpret(user_message)
                )
                used = False
        else:
            response_text = local_interpret(user_message)
            conversation_id = conversation_id or f"local-{run_id}"
            used = False

        run = CassandraRun(
            run_id=run_id,
            conversation_id=conversation_id,
            user_message=user_message,
            cassandra_response=response_text,
            epistemic_classification=self._classify_epistemic(response_text),
            gate_status=self._classify_gate(response_text),
            created_at=ts,
            used_base44=used,
            metadata={"mode": self.mode, "system_prompt_chars": len(self.system_prompt)},
        )
        self.runs.append(run)

        if persist and self.is_base44:
            try:
                self.base44.create_entity("CassandraRun", {
                    "intent_id": None,
                    "profile_id": None,
                    "input_summary": user_message[:200],
                    "context_refs": [],
                    "memory_refs": [],
                    "proposed_output": response_text[:2000],
                    "epistemic_classification": run.epistemic_classification,
                    "suggested_decision": run.gate_status,
                    "gate_status": run.gate_status,
                    "run_status": "COMPLETED",
                    "created_at": ts * 1000,
                })
            except Base44Error:
                pass  # do not fail chat on persistence error

        return run

    def system_prompt_text(self) -> str:
        return self.system_prompt
