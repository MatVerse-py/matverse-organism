from __future__ import annotations

import os
import re
import shlex
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    risk: str
    reason: str
    requires_approval: bool = False


class Policy:
    _always_blocked = (
        re.compile(r"(^|\s)rm\s+-[^\n]*r[^\n]*f[^\n]*\s+/(\s|$)"),
        re.compile(r"(^|\s)(mkfs|fdisk|parted)(\s|$)"),
        re.compile(r"(^|\s)dd\s+.*\bof=/dev/"),
        re.compile(r":\(\)\s*\{\s*:\|:&\s*;\s*\}\s*;\s*:"),
        re.compile(r"(^|\s)(shutdown|reboot|poweroff|halt)(\s|$)"),
        re.compile(r"(^|\s)sudo(\s|$)"),
        re.compile(r"curl\b[^|\n]*\|\s*(sh|bash|zsh)\b"),
        re.compile(r"wget\b[^|\n]*\|\s*(sh|bash|zsh)\b"),
        re.compile(r"git\s+push\s+.*(--force|-f)(\s|$)"),
    )
    _high_risk = (
        re.compile(r"(^|\s)git\s+reset\s+--hard(\s|$)"),
        re.compile(r"(^|\s)git\s+clean\s+-[^\n]*f"),
        re.compile(r"(^|\s)docker\s+system\s+prune"),
        re.compile(r"(^|\s)(pip|pip3|npm|pnpm|yarn|uv)\s+publish(\s|$)"),
        re.compile(r"(^|\s)git\s+push(\s|$)"),
        re.compile(r"(^|\s)git\s+commit(\s|$)"),
        re.compile(r"(^|\s)rm\s+"),
    )
    _secret_names = (
        "token",
        "secret",
        "password",
        "passwd",
        "api_key",
        "apikey",
        "private_key",
        "authorization",
        "cookie",
    )

    def __init__(self, workspace: Path, approval_mode: str = "on-risk") -> None:
        self.workspace = workspace.resolve()
        self.approval_mode = approval_mode

    def resolve_path(self, candidate: str | Path, *, must_exist: bool = False) -> Path:
        path = Path(candidate)
        resolved = (
            path.expanduser().resolve()
            if path.is_absolute()
            else (self.workspace / path).resolve()
        )
        if resolved != self.workspace and self.workspace not in resolved.parents:
            raise PermissionError(f"Path escapes workspace: {candidate}")
        if must_exist and not resolved.exists():
            raise FileNotFoundError(resolved)
        return resolved

    def command(self, command: str) -> Decision:
        normalized = command.strip()
        if not normalized:
            return Decision(False, "LOW", "Empty command")
        if "\x00" in normalized or "\n" in normalized:
            return Decision(False, "CRITICAL", "NUL and multiline commands are blocked")
        for pattern in self._always_blocked:
            if pattern.search(normalized):
                return Decision(False, "CRITICAL", f"Blocked pattern: {pattern.pattern}")

        try:
            tokens = shlex.split(normalized, posix=os.name != "nt")
        except ValueError as exc:
            return Decision(False, "HIGH", f"Invalid shell syntax: {exc}")

        for token in tokens:
            if token.startswith(("/", "~")):
                try:
                    self.resolve_path(token)
                except (PermissionError, OSError):
                    return Decision(False, "CRITICAL", f"External path blocked: {token}")
            if token == ".." or token.startswith("../") or "/../" in token:
                return Decision(False, "CRITICAL", f"Parent traversal blocked: {token}")

        risk = "LOW"
        if any(pattern.search(normalized) for pattern in self._high_risk):
            risk = "HIGH"
        elif any(symbol in normalized for symbol in (">", "|", "&&", ";")):
            risk = "MEDIUM"

        requires_approval = self.approval_mode == "always" or (
            self.approval_mode == "on-risk" and risk in {"HIGH", "CRITICAL"}
        )
        return Decision(True, risk, "Command allowed by workspace policy", requires_approval)

    def redact(self, value: object) -> object:
        if isinstance(value, dict):
            redacted: dict[str, object] = {}
            for key, child in value.items():
                if any(name in key.lower() for name in self._secret_names):
                    redacted[key] = "<redacted>"
                else:
                    redacted[key] = self.redact(child)
            return redacted
        if isinstance(value, list):
            return [self.redact(child) for child in value]
        if isinstance(value, str):
            value = re.sub(r"\b(sk-[A-Za-z0-9_-]{12,})\b", "<redacted-token>", value)
            value = re.sub(r"\b(gh[pousr]_[A-Za-z0-9]{20,})\b", "<redacted-token>", value)
            value = re.sub(r"\b(hf_[A-Za-z0-9]{20,})\b", "<redacted-token>", value)
            value = re.sub(
                r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b",
                "<redacted-jwt>",
                value,
            )
        return value
