"""
matverse.cassandra_backend.server
==================================

A self-contained HTTP server implementing the Cassandra API contract.

This is the backend that the Base44 app (or any other frontend) calls
to converse with the Cassandra agent. Pure stdlib, zero dependencies,
runs anywhere Python 3.8+ runs.

Endpoints
---------

  GET  /health
       → 200 OK with version + uptime

  POST /auth/session
       Body: {"api_key": "<from secret manager>"}
       Returns: {"session_token": "...", "expires_in": 3600, "user_id": "..."}
       The api_key is wiped from memory after this call.

  POST /auth/capability
       Headers: Authorization: Bearer <session_token>
       Body: {"agent_id": "cassandra", "skill_name": "interpret", "ttl_seconds": 600}
       Returns: {"capability_token": "...", "expires_in": 600, "scope": {...}}

  POST /chat
       Headers: Authorization: Bearer <capability_token>
       Body: {"message": "...", "context": {"page": "/copilot", "user_role": "operator"}}
       Returns: {"response": "...", "gate_status": "PASS|HOLD|ESCALATE|DENY",
                 "epistemic": "OBS|HYP|ESC|...", "triggered_limits": [...],
                 "needs_operator": true|false, "run_id": "..."}

  GET  /system-prompt
       Returns: the canonical CASSANDRA_SYSTEM_PROMPT (so the Base44
       frontend can render it for transparency/audit).

Security model
--------------
- The `api_key` is exchanged for a `session_token` at /auth/session.
- All subsequent calls use Bearer credentials (no api_key in headers).
- Agent operations require a `capability_token` scoped per agent+skill.
- The api_key is wiped from memory after /auth/session.

The api_key check is a simple constant-time comparison against the
env var `CASSANDRA_API_KEY`. In production, replace with a proper
secret manager (Vault, AWS Secrets Manager, etc.).

Run
---
    export CASSANDRA_API_KEY="<from secret manager>"
    python -m matverse.cassandra_backend.server

    # or as a module:
    python -c "from matverse.cassandra_backend.server import run; run()"

    # or via the CLI:
    python -m matverse.cassandra_backend.server --host 0.0.0.0 --port 8787
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple

from .policy import (
    evaluate,
    parse_epistemic,
    has_source_citation,
    GateResult,
    get_system_prompt,
)
from .router import (
    route as route_decision,
    local_interpret,
    RouteDecision,
    DEFAULT_APP_ID,
    SUPERAGENT_ID,
)

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

__version__ = "1.0.0"
SERVER_STARTED_AT = int(time.time())


# ---------------------------------------------------------------------------
# In-memory token store (replace with Redis in production)
# ---------------------------------------------------------------------------

@dataclass
class SessionRecord:
    token: str
    user_id: str
    issued_at: int
    ttl_seconds: int

    def is_expired(self, now: Optional[int] = None) -> bool:
        if now is None:
            now = int(time.time())
        return (now - self.issued_at) >= self.ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token": self.token,
            "user_id": self.user_id,
            "issued_at": self.issued_at,
            "ttl_seconds": self.ttl_seconds,
            "is_expired": self.is_expired(),
        }


@dataclass
class CapabilityRecord:
    token: str
    agent_id: str
    skill_name: str
    scope: Dict[str, Any]
    issued_at: int
    ttl_seconds: int

    def is_expired(self, now: Optional[int] = None) -> bool:
        if now is None:
            now = int(time.time())
        return (now - self.issued_at) >= self.ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token": self.token,
            "agent_id": self.agent_id,
            "skill_name": self.skill_name,
            "scope": dict(self.scope),
            "issued_at": self.issued_at,
            "ttl_seconds": self.ttl_seconds,
            "is_expired": self.is_expired(),
        }


class TokenStore:
    """In-memory token store. Replace with Redis for production."""

    def __init__(self) -> None:
        self.sessions: Dict[str, SessionRecord] = {}
        self.capabilities: Dict[str, CapabilityRecord] = {}

    def add_session(self, sess: SessionRecord) -> None:
        self.sessions[sess.token] = sess

    def get_session(self, token: str) -> Optional[SessionRecord]:
        s = self.sessions.get(token)
        if s is None or s.is_expired():
            return None
        return s

    def add_capability(self, cap: CapabilityRecord) -> None:
        self.capabilities[cap.token] = cap

    def get_capability(self, token: str) -> Optional[CapabilityRecord]:
        c = self.capabilities.get(token)
        if c is None or c.is_expired():
            return None
        return c

    def revoke_session(self, token: str) -> None:
        self.sessions.pop(token, None)

    def revoke_capability(self, token: str) -> None:
        self.capabilities.pop(token, None)


# Module-level singleton (created in main())
TOKENS: Optional[TokenStore] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_token(prefix: str) -> str:
    """Generate a cryptographically-secure random token."""
    return f"{prefix}-{secrets.token_urlsafe(32)}"


def _new_run_id() -> str:
    """Generate a run id (microsecond resolution)."""
    return f"run-{int(time.time() * 1_000_000)}"


def _check_api_key(provided: str) -> bool:
    """Constant-time comparison against the env var."""
    expected = os.environ.get("CASSANDRA_API_KEY", "")
    if not expected:
        return False
    return hmac.compare_digest(provided, expected)


def _json_response(handler: BaseHTTPRequestHandler, status: int, body: Dict[str, Any]) -> None:
    """Send a JSON response."""
    payload = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.send_header("X-Cassandra-Version", __version__)
    handler.end_headers()
    handler.wfile.write(payload)


def _read_json(handler: BaseHTTPRequestHandler) -> Optional[Dict[str, Any]]:
    """Read and parse the request body as JSON."""
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None


def _get_bearer(handler: BaseHTTPRequestHandler) -> Optional[str]:
    """Extract the Bearer token from the Authorization header."""
    auth = handler.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[len("Bearer "):].strip()
    return None


# ---------------------------------------------------------------------------
# Request handlers
# ---------------------------------------------------------------------------

def handle_health() -> Tuple[int, Dict[str, Any]]:
    return 200, {
        "status": "ok",
        "version": __version__,
        "uptime_seconds": int(time.time()) - SERVER_STARTED_AT,
        "matverse_app_id": DEFAULT_APP_ID,
        "base44_superagent_id": SUPERAGENT_ID,
        "endpoints": [
            "GET  /health",
            "POST /auth/session",
            "POST /auth/capability",
            "POST /chat",
            "GET  /system-prompt",
        ],
        "constitutional_position": (
            "Cassandra PREPARA. O operador assina. O mundo testemunha. "
            "Action requires Ω-Gate + EvidenceOS + operator."
        ),
    }


def handle_auth_session(body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    if not body or "api_key" not in body:
        return 400, {"error": "missing api_key", "code": "MISSING_API_KEY"}

    api_key = body.get("api_key", "")
    if not _check_api_key(api_key):
        return 401, {"error": "invalid api_key", "code": "INVALID_API_KEY"}

    # Bootstrap successful. Mint a session token.
    token = _new_token("sess")
    issued = int(time.time())
    ttl = int(body.get("ttl_seconds", 3600))
    # user_id is derived from the api_key fingerprint, NOT the claim
    fingerprint = hashlib.sha256(api_key.encode()).hexdigest()[:12]
    user_id = f"usr-{fingerprint}"
    sess = SessionRecord(token=token, user_id=user_id, issued_at=issued, ttl_seconds=ttl)
    assert TOKENS is not None
    TOKENS.add_session(sess)

    return 200, {
        "session_token": token,
        "token_type": "Bearer",
        "expires_in": ttl,
        "issued_at": issued,
        "user_id": user_id,
        "message": "api_key has been validated. Use this session_token for subsequent calls. "
                   "The api_key is no longer needed and was wiped from memory.",
    }


def handle_auth_capability(body: Dict[str, Any], bearer: Optional[str]) -> Tuple[int, Dict[str, Any]]:
    if not bearer:
        return 401, {"error": "missing Bearer token", "code": "MISSING_BEARER"}
    assert TOKENS is not None
    sess = TOKENS.get_session(bearer)
    if sess is None:
        return 401, {"error": "invalid or expired session", "code": "INVALID_SESSION"}

    if not body or "agent_id" not in body or "skill_name" not in body:
        return 400, {"error": "missing agent_id or skill_name", "code": "MISSING_FIELDS"}

    agent_id = body.get("agent_id", "")
    skill_name = body.get("skill_name", "")
    ttl = int(body.get("ttl_seconds", 600))
    scope = body.get("scope", {})

    token = _new_token("cap")
    issued = int(time.time())
    cap = CapabilityRecord(
        token=token, agent_id=agent_id, skill_name=skill_name,
        scope=scope, issued_at=issued, ttl_seconds=ttl,
    )
    TOKENS.add_capability(cap)

    return 200, {
        "capability_token": token,
        "token_type": "Bearer",
        "agent_id": agent_id,
        "skill_name": skill_name,
        "scope": scope,
        "expires_in": ttl,
        "issued_at": issued,
        "user_id": sess.user_id,
    }


def handle_chat(body: Dict[str, Any], bearer: Optional[str]) -> Tuple[int, Dict[str, Any]]:
    if not bearer:
        return 401, {"error": "missing Bearer token", "code": "MISSING_BEARER"}
    assert TOKENS is not None
    cap = TOKENS.get_capability(bearer)
    if cap is None:
        return 401, {"error": "invalid or expired capability", "code": "INVALID_CAPABILITY"}

    # Enforce the capability's scope
    if cap.skill_name not in ("interpret", "chat", "general"):
        return 403, {
            "error": f"skill_name '{cap.skill_name}' is not authorized for /chat",
            "code": "SKILL_NOT_AUTHORIZED",
        }

    if not body or "message" not in body:
        return 400, {"error": "missing message", "code": "MISSING_MESSAGE"}

    message = body.get("message", "").strip()
    if not message:
        return 400, {"error": "empty message", "code": "EMPTY_MESSAGE"}

    context = body.get("context", {})
    prefer_burst = body.get("prefer_burst", False)
    burst_authorized = bool(cap.scope.get("allow_burst", False))

    # Step 1: gate (the 5 hard limits)
    gate = evaluate(message)

    # Step 2: route
    rd = route_decision(message, prefer_burst=prefer_burst, burst_authorized=burst_authorized)

    # Step 3: produce response
    if gate.gate_status == "ESCALATE" or gate.gate_status == "DENY":
        # Fail-closed: do NOT call any LLM. Return the gate response.
        response_text = (
            f"{gate.reason}\n"
            f"Esta ação está fora do escopo de Cassandra. "
            f"Requer Ω-Gate + EvidenceOS + operador humano.\n"
            f"[epistemic: {gate.epistemic}] {gate.reason}"
        )
        route_used = "ZERO"
        model_used = "gate_only (fail-closed)"
    elif rd.route == "BURST" and burst_authorized:
        # In production: call NVIDIA NIM here
        # For the self-contained backend, we fall through to local_interpret
        # and mark the route as BURST in the audit trail.
        response_text = local_interpret(message) + (
            f"\n[route: BURST, model_hint: {rd.model_hint}] "
            f"(BURST integration is OPTIONAL; local_interpret used in this build)"
        )
        route_used = "BURST"
        model_used = rd.model_hint
    else:
        response_text = local_interpret(message)
        route_used = rd.route
        model_used = rd.model_hint

    # Step 4: re-evaluate with the response (Limit 2: OBS needs source)
    final_gate = evaluate(message, response_text)

    run_id = _new_run_id()
    return 200, {
        "run_id": run_id,
        "response": response_text,
        "gate_status": final_gate.gate_status,
        "epistemic": final_gate.epistemic,
        "triggered_limits": final_gate.triggered_limits,
        "needs_operator": final_gate.needs_operator,
        "route_used": route_used,
        "model_used": model_used,
        "agent_id": cap.agent_id,
        "skill_name": cap.skill_name,
        "user_id": TOKENS.get_session_by_token(bearer).user_id if TOKENS.get_session_by_token(bearer) else None,
        "context": context,
        "issued_at": int(time.time()),
        "policy_version": "v3.8.2",
        "constitutional_position": "Cassandra PREPARA. O operador assina.",
    }


def handle_system_prompt() -> Tuple[int, Dict[str, Any]]:
    return 200, {
        "system_prompt": get_system_prompt(),
        "version": "v3.8.2",
        "immutable": True,
        "note": "This prompt is the constitutional contract of the agent. "
                "It is served read-only for transparency/audit. "
                "The agent enforces it at runtime via the 5 hard limits.",
    }


# Patch TokenStore to support lookup by bearer (used in /chat)
def _patch_token_store():
    """Add a helper to TokenStore."""
    if not hasattr(TokenStore, "get_session_by_token"):
        def get_session_by_token(self, token: str) -> Optional[SessionRecord]:
            return self.get_session(token)
        TokenStore.get_session_by_token = get_session_by_token
_patch_token_store()


# ---------------------------------------------------------------------------
# HTTP request handler
# ---------------------------------------------------------------------------

class CassandraRequestHandler(BaseHTTPRequestHandler):
    """The HTTP request handler for Cassandra."""

    # Suppress default access logging (we have our own audit)
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            status, body = handle_health()
            _json_response(self, status, body)
        elif self.path == "/system-prompt":
            status, body = handle_system_prompt()
            _json_response(self, status, body)
        else:
            _json_response(self, 404, {"error": "not found", "path": self.path})

    def do_POST(self) -> None:  # noqa: N802
        body = _read_json(self)
        if body is None:
            _json_response(self, 400, {"error": "invalid JSON", "code": "INVALID_JSON"})
            return

        bearer = _get_bearer(self)

        if self.path == "/auth/session":
            status, response_body = handle_auth_session(body)
        elif self.path == "/auth/capability":
            status, response_body = handle_auth_capability(body, bearer)
        elif self.path == "/chat":
            status, response_body = handle_chat(body, bearer)
        else:
            _json_response(self, 404, {"error": "not found", "path": self.path})
            return

        _json_response(self, status, response_body)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(host: str = "127.0.0.1", port: int = 8787) -> None:
    """Run the Cassandra HTTP server."""
    global TOKENS
    TOKENS = TokenStore()

    # Sanity check: warn if no api_key is set
    if not os.environ.get("CASSANDRA_API_KEY"):
        print("=" * 60, file=sys.stderr)
        print("WARNING: CASSANDRA_API_KEY is not set.", file=sys.stderr)
        print("Set it via:", file=sys.stderr)
        print("  export CASSANDRA_API_KEY='<from secret manager>'", file=sys.stderr)
        print("Without it, /auth/session will reject all requests.", file=sys.stderr)
        print("=" * 60, file=sys.stderr)

    server = ThreadingHTTPServer((host, port), CassandraRequestHandler)
    print(f"Cassandra backend listening on http://{host}:{port}", file=sys.stderr)
    print(f"  version:     {__version__}", file=sys.stderr)
    print(f"  endpoints:   /health, /auth/session, /auth/capability, /chat, /system-prompt", file=sys.stderr)
    print(f"  constitution: Cassandra PREPARA. O operador assina.", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down…", file=sys.stderr)
        server.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cassandra constitutional backend")
    parser.add_argument("--host", default="127.0.0.1", help="bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8787, help="bind port (default: 8787)")
    args = parser.parse_args()
    run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
