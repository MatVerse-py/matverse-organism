"""
matverse.cassandra_agent
========================

High-level facade. Re-exports the most useful symbols so callers can do:

    from matverse import CassandraAgent, Base44Client, local_interpret

All actual code lives in `cassandra_prompt` and `cassandra_base44`.
"""

from .cassandra_prompt import (
    CASSANDRA_SYSTEM_PROMPT,
    ROLE,
    SCOPE,
    ADMISSIBILITY,
    EPITEMIC,
    CANONICAL_CORPUS,
)
from .cassandra_base44 import (
    Base44Client,
    Base44Error,
    CassandraAgent,
    CassandraRun,
    DEFAULT_APP_ID,
    DEFAULT_BASE_URL,
    DEFAULT_OSX_CHAT_AGENT,
    API_KEY_ENV,
    local_interpret,
)

__all__ = [
    "CASSANDRA_SYSTEM_PROMPT", "ROLE", "SCOPE", "ADMISSIBILITY", "EPITEMIC", "CANONICAL_CORPUS",
    "Base44Client", "Base44Error", "CassandraAgent", "CassandraRun",
    "DEFAULT_APP_ID", "DEFAULT_BASE_URL", "DEFAULT_OSX_CHAT_AGENT", "API_KEY_ENV",
    "local_interpret",
]
