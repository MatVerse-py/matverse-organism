"""
matverse.cassandra_backend
==========================

A self-contained HTTP backend for the Cassandra agent.

The Base44 frontend (or any other client) can call this backend to
converse with the constitutional Cassandra agent. Pure stdlib,
zero dependencies, runs anywhere Python 3.8+ runs.

See:
  - server.py      — the HTTP server
  - policy.py      — the 5 hard limits
  - router.py      — the LLM router (ZERO/TINY/BURST)
  - README.md      — quickstart
  - ../../../references/cassandra_backend_api.md — full API contract
"""

from .server import (
    run, main, __version__,
    CassandraRequestHandler, TokenStore,
    SessionRecord, CapabilityRecord,
    handle_health, handle_auth_session, handle_auth_capability,
    handle_chat, handle_system_prompt,
)
from .policy import (
    evaluate, parse_epistemic, has_source_citation,
    check_external_action, check_uncertainty, check_impersonation,
    GateResult, get_system_prompt,
)
from .router import (
    route as route_decision, local_interpret, complexity_score,
    RouteDecision, DEFAULT_APP_ID, SUPERAGENT_ID,
)

__all__ = [
    # server
    "run", "main", "__version__", "CassandraRequestHandler", "TokenStore",
    "SessionRecord", "CapabilityRecord",
    "handle_health", "handle_auth_session", "handle_auth_capability",
    "handle_chat", "handle_system_prompt",
    # policy
    "evaluate", "parse_epistemic", "has_source_citation",
    "check_external_action", "check_uncertainty", "check_impersonation",
    "GateResult", "get_system_prompt",
    # router
    "route_decision", "local_interpret", "complexity_score",
    "RouteDecision", "DEFAULT_APP_ID", "SUPERAGENT_ID",
]
