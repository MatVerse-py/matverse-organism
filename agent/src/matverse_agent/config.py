from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


_TRUE = {"1", "true", "yes", "on"}


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUE


def _int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    value = default if raw is None else int(raw)
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    workspace: Path
    model: str = "qwen3:4b"
    ollama_url: str = "http://127.0.0.1:11434"
    searxng_url: str | None = None
    max_steps: int = 32
    command_timeout_seconds: int = 180
    max_output_chars: int = 60_000
    network_enabled: bool = False
    shell_enabled: bool = True
    approval_mode: str = "on-risk"
    host: str = "127.0.0.1"
    port: int = 8766

    @property
    def state_dir(self) -> Path:
        return self.workspace / ".matverse"

    @property
    def runs_dir(self) -> Path:
        return self.state_dir / "runs"

    @property
    def database_path(self) -> Path:
        return self.state_dir / "state.db"

    @classmethod
    def from_env(
        cls,
        workspace: str | Path | None = None,
        approval_mode: str | None = None,
    ) -> "Settings":
        resolved = Path(
            workspace or os.getenv("MATVERSE_WORKSPACE", os.getcwd())
        ).expanduser().resolve()
        mode = approval_mode or os.getenv("MATVERSE_APPROVAL_MODE", "on-risk")
        if mode not in {"always", "on-risk", "never"}:
            raise ValueError("approval_mode must be always, on-risk or never")
        settings = cls(
            workspace=resolved,
            model=os.getenv("MATVERSE_MODEL", "qwen3:4b"),
            ollama_url=os.getenv("MATVERSE_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/"),
            searxng_url=(os.getenv("MATVERSE_SEARXNG_URL") or None),
            max_steps=_int_env("MATVERSE_MAX_STEPS", 32, 1, 256),
            command_timeout_seconds=_int_env(
                "MATVERSE_COMMAND_TIMEOUT", 180, 1, 3600
            ),
            max_output_chars=_int_env(
                "MATVERSE_MAX_OUTPUT_CHARS", 60_000, 1_000, 2_000_000
            ),
            network_enabled=_bool_env("MATVERSE_NETWORK_ENABLED", False),
            shell_enabled=_bool_env("MATVERSE_SHELL_ENABLED", True),
            approval_mode=mode,
            host=os.getenv("MATVERSE_HOST", "127.0.0.1"),
            port=_int_env("MATVERSE_PORT", 8766, 1024, 65535),
        )
        settings.workspace.mkdir(parents=True, exist_ok=True)
        settings.runs_dir.mkdir(parents=True, exist_ok=True)
        return settings
