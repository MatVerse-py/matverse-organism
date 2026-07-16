from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import httpx

from .artifacts import create_mobile_pwa, create_slides, create_video, create_website
from .config import Settings
from .ledger import Ledger
from .policy import Policy


JSON = dict[str, Any]
ApprovalCallback = Callable[[str, str], bool]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    parameters: JSON
    handler: Callable[..., JSON]

    def schema(self) -> JSON:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(
        self,
        settings: Settings,
        ledger: Ledger,
        run_id: str,
        approval_callback: ApprovalCallback | None = None,
    ) -> None:
        self.settings = settings
        self.policy = Policy(settings.workspace, settings.approval_mode)
        self.ledger = ledger
        self.run_id = run_id
        self.approval_callback = approval_callback
        self._tools = self._build_tools()

    @property
    def schemas(self) -> list[JSON]:
        return [tool.schema() for tool in self._tools.values()]

    @property
    def names(self) -> list[str]:
        return sorted(self._tools)

    def execute(self, name: str, arguments: JSON) -> JSON:
        tool = self._tools.get(name)
        if tool is None:
            result = {"status": "BLOCK", "error": f"Unknown tool: {name}"}
        else:
            try:
                result = tool.handler(**arguments)
                if not isinstance(result, dict):
                    result = {"status": "PASS", "result": result}
            except Exception as exc:  # tool boundary must convert exceptions to evidence
                result = {
                    "status": "BLOCK",
                    "error": f"{type(exc).__name__}: {exc}",
                }
        self.ledger.append(
            self.run_id,
            "TOOL_RESULT",
            {
                "tool": name,
                "arguments": self.policy.redact(arguments),
                "result": self.policy.redact(result),
            },
        )
        return result

    def _build_tools(self) -> dict[str, ToolSpec]:
        object_schema = {"type": "object", "additionalProperties": False}
        specs = [
            ToolSpec(
                "list_files",
                "List files inside the workspace using a glob pattern.",
                {
                    **object_schema,
                    "properties": {
                        "pattern": {"type": "string", "default": "**/*"},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 2000},
                    },
                },
                self.list_files,
            ),
            ToolSpec(
                "read_file",
                "Read a UTF-8 text file with optional 1-based line bounds.",
                {
                    **object_schema,
                    "required": ["path"],
                    "properties": {
                        "path": {"type": "string"},
                        "start_line": {"type": "integer", "minimum": 1},
                        "end_line": {"type": "integer", "minimum": 1},
                    },
                },
                self.read_file,
            ),
            ToolSpec(
                "write_file",
                "Write a UTF-8 file inside the workspace.",
                {
                    **object_schema,
                    "required": ["path", "content"],
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                        "overwrite": {"type": "boolean", "default": False},
                    },
                },
                self.write_file,
            ),
            ToolSpec(
                "replace_text",
                "Replace exact text in a workspace file and fail if the target is absent.",
                {
                    **object_schema,
                    "required": ["path", "old", "new"],
                    "properties": {
                        "path": {"type": "string"},
                        "old": {"type": "string"},
                        "new": {"type": "string"},
                        "count": {"type": "integer", "minimum": 0, "default": 0},
                    },
                },
                self.replace_text,
            ),
            ToolSpec(
                "search_text",
                "Search case-insensitively across text files in the workspace.",
                {
                    **object_schema,
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string"},
                        "glob": {"type": "string", "default": "**/*"},
                        "max_results": {"type": "integer", "minimum": 1, "maximum": 500},
                    },
                },
                self.search_text,
            ),
            ToolSpec(
                "run_command",
                "Run a shell command inside the workspace under the constitutional policy.",
                {
                    **object_schema,
                    "required": ["command"],
                    "properties": {
                        "command": {"type": "string"},
                        "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 3600},
                    },
                },
                self.run_command,
            ),
            ToolSpec(
                "git_status",
                "Return concise Git status for the workspace.",
                object_schema,
                self.git_status,
            ),
            ToolSpec(
                "git_diff",
                "Return a bounded Git diff for the workspace.",
                {
                    **object_schema,
                    "properties": {"staged": {"type": "boolean", "default": False}},
                },
                self.git_diff,
            ),
            ToolSpec(
                "create_worktree",
                "Create an isolated Git worktree under .matverse/worktrees.",
                {
                    **object_schema,
                    "required": ["branch"],
                    "properties": {
                        "branch": {"type": "string"},
                        "base_ref": {"type": "string", "default": "HEAD"},
                    },
                },
                self.create_worktree,
            ),
            ToolSpec(
                "http_get",
                "Fetch an HTTP or HTTPS URL when network access is enabled.",
                {
                    **object_schema,
                    "required": ["url"],
                    "properties": {
                        "url": {"type": "string"},
                        "max_bytes": {"type": "integer", "minimum": 1024, "maximum": 5000000},
                    },
                },
                self.http_get,
            ),
            ToolSpec(
                "web_search",
                "Search the web through the configured local SearXNG instance.",
                {
                    **object_schema,
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    },
                },
                self.web_search,
            ),
            ToolSpec(
                "browser_snapshot",
                "Open a page with local Playwright and save screenshot plus visible text.",
                {
                    **object_schema,
                    "required": ["url", "name"],
                    "properties": {
                        "url": {"type": "string"},
                        "name": {"type": "string"},
                    },
                },
                self.browser_snapshot,
            ),
            ToolSpec(
                "create_website",
                "Generate a complete static website artifact.",
                {
                    **object_schema,
                    "required": ["name", "title", "sections"],
                    "properties": {
                        "name": {"type": "string"},
                        "title": {"type": "string"},
                        "sections": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["heading", "body"],
                                "properties": {
                                    "heading": {"type": "string"},
                                    "body": {"type": "string"},
                                },
                            },
                        },
                    },
                },
                self._create_website,
            ),
            ToolSpec(
                "create_mobile_pwa",
                "Generate an installable offline-first mobile PWA.",
                {
                    **object_schema,
                    "required": ["name", "title", "features"],
                    "properties": {
                        "name": {"type": "string"},
                        "title": {"type": "string"},
                        "features": {"type": "array", "items": {"type": "string"}},
                    },
                },
                self._create_mobile_pwa,
            ),
            ToolSpec(
                "create_slides",
                "Generate a real PPTX presentation locally.",
                {
                    **object_schema,
                    "required": ["name", "title", "slides"],
                    "properties": {
                        "name": {"type": "string"},
                        "title": {"type": "string"},
                        "slides": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["title", "bullets"],
                                "properties": {
                                    "title": {"type": "string"},
                                    "bullets": {"type": "array", "items": {"type": "string"}},
                                },
                            },
                        },
                    },
                },
                self._create_slides,
            ),
            ToolSpec(
                "create_video",
                "Generate a local MP4 from scene cards using Pillow and FFmpeg.",
                {
                    **object_schema,
                    "required": ["name", "scenes"],
                    "properties": {
                        "name": {"type": "string"},
                        "scenes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["title", "body"],
                                "properties": {
                                    "title": {"type": "string"},
                                    "body": {"type": "string"},
                                    "duration": {"type": "number", "minimum": 0.5, "maximum": 60},
                                },
                            },
                        },
                    },
                },
                self._create_video,
            ),
        ]
        return {spec.name: spec for spec in specs}

    def list_files(self, pattern: str = "**/*", limit: int = 500) -> JSON:
        if ".." in Path(pattern).parts:
            raise PermissionError("Parent traversal is blocked")
        rows: list[JSON] = []
        for path in sorted(self.settings.workspace.glob(pattern)):
            if any(part in {".git", "__pycache__"} for part in path.parts):
                continue
            relative = path.relative_to(self.settings.workspace).as_posix()
            rows.append(
                {
                    "path": relative,
                    "type": "directory" if path.is_dir() else "file",
                    "bytes": path.stat().st_size if path.is_file() else None,
                }
            )
            if len(rows) >= limit:
                break
        return {"status": "PASS", "items": rows, "truncated": len(rows) >= limit}

    def read_file(
        self,
        path: str,
        start_line: int = 1,
        end_line: int | None = None,
    ) -> JSON:
        target = self.policy.resolve_path(path, must_exist=True)
        if not target.is_file():
            raise IsADirectoryError(target)
        if target.stat().st_size > 10_000_000:
            raise ValueError("File exceeds 10 MB text-read limit")
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        stop = len(lines) if end_line is None else min(end_line, len(lines))
        if stop < start_line:
            raise ValueError("end_line must be greater than or equal to start_line")
        selected = lines[start_line - 1 : stop]
        content = "\n".join(f"{number}: {line}" for number, line in enumerate(selected, start_line))
        return {
            "status": "PASS",
            "path": target.relative_to(self.settings.workspace).as_posix(),
            "start_line": start_line,
            "end_line": stop,
            "total_lines": len(lines),
            "content": self._limit(content),
        }

    def write_file(self, path: str, content: str, overwrite: bool = False) -> JSON:
        target = self.policy.resolve_path(path)
        if target.exists() and not overwrite:
            return {"status": "BLOCK", "error": "File exists; set overwrite=true"}
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return {
            "status": "PASS",
            "path": target.relative_to(self.settings.workspace).as_posix(),
            "bytes": len(content.encode("utf-8")),
            "sha256": digest,
        }

    def replace_text(self, path: str, old: str, new: str, count: int = 0) -> JSON:
        target = self.policy.resolve_path(path, must_exist=True)
        text = target.read_text(encoding="utf-8")
        occurrences = text.count(old)
        if occurrences == 0:
            return {"status": "BLOCK", "error": "Target text not found"}
        updated = text.replace(old, new, count if count > 0 else -1)
        target.write_text(updated, encoding="utf-8")
        replacements = min(occurrences, count) if count > 0 else occurrences
        return {
            "status": "PASS",
            "path": target.relative_to(self.settings.workspace).as_posix(),
            "replacements": replacements,
            "sha256": hashlib.sha256(updated.encode("utf-8")).hexdigest(),
        }

    def search_text(self, query: str, glob: str = "**/*", max_results: int = 100) -> JSON:
        needle = query.casefold()
        results: list[JSON] = []
        for path in self.settings.workspace.glob(glob):
            if not path.is_file() or any(part in {".git", ".matverse"} for part in path.parts):
                continue
            if path.stat().st_size > 5_000_000:
                continue
            try:
                lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            for line_number, line in enumerate(lines, 1):
                if needle in line.casefold():
                    results.append(
                        {
                            "path": path.relative_to(self.settings.workspace).as_posix(),
                            "line": line_number,
                            "text": line[:500],
                        }
                    )
                    if len(results) >= max_results:
                        return {"status": "PASS", "results": results, "truncated": True}
        return {"status": "PASS", "results": results, "truncated": False}

    def run_command(self, command: str, timeout_seconds: int | None = None) -> JSON:
        if not self.settings.shell_enabled:
            return {"status": "BLOCK", "error": "Shell is disabled"}
        decision = self.policy.command(command)
        if not decision.allowed:
            return {"status": "BLOCK", "risk": decision.risk, "error": decision.reason}
        if decision.requires_approval:
            if self.approval_callback is None or not self.approval_callback(command, decision.risk):
                return {"status": "HOLD", "risk": decision.risk, "error": "Approval required"}
        timeout = timeout_seconds or self.settings.command_timeout_seconds
        process = subprocess.run(
            command,
            cwd=self.settings.workspace,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=os.environ.copy(),
            check=False,
        )
        return {
            "status": "PASS" if process.returncode == 0 else "BLOCK",
            "risk": decision.risk,
            "exit_code": process.returncode,
            "stdout": self._limit(process.stdout),
            "stderr": self._limit(process.stderr),
        }

    def git_status(self) -> JSON:
        return self.run_command("git status --short --branch")

    def git_diff(self, staged: bool = False) -> JSON:
        command = "git diff --cached --" if staged else "git diff --"
        return self.run_command(command)

    def create_worktree(self, branch: str, base_ref: str = "HEAD") -> JSON:
        if not re.fullmatch(r"[A-Za-z0-9._/-]{1,120}", branch) or ".." in branch:
            raise ValueError("Invalid branch name")
        slug = re.sub(r"[^A-Za-z0-9._-]+", "-", branch).strip("-")
        target = self.settings.state_dir / "worktrees" / slug
        target.parent.mkdir(parents=True, exist_ok=True)
        command = f"git worktree add -b {branch} {target.as_posix()} {base_ref}"
        result = self.run_command(command)
        result["path"] = str(target)
        return result

    def http_get(self, url: str, max_bytes: int = 1_000_000) -> JSON:
        self._require_network()
        self._validate_url(url)
        with httpx.Client(follow_redirects=True, timeout=30) as client:
            response = client.get(url, headers={"User-Agent": "MatVerse-Agent/1.0"})
            response.raise_for_status()
            content = response.content[:max_bytes]
        content_type = response.headers.get("content-type", "")
        if "text" in content_type or "json" in content_type or not content_type:
            body: object = content.decode(response.encoding or "utf-8", errors="replace")
        else:
            body = {"binary_bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
        return {
            "status": "PASS",
            "url": str(response.url),
            "http_status": response.status_code,
            "content_type": content_type,
            "body": self._limit(body) if isinstance(body, str) else body,
            "truncated": len(response.content) > max_bytes,
        }

    def web_search(self, query: str, limit: int = 10) -> JSON:
        self._require_network()
        if not self.settings.searxng_url:
            return {"status": "HOLD", "error": "MATVERSE_SEARXNG_URL is not configured"}
        endpoint = self.settings.searxng_url.rstrip("/") + "/search"
        with httpx.Client(timeout=30) as client:
            response = client.get(
                endpoint,
                params={"q": query, "format": "json", "language": "all", "safesearch": 1},
                headers={"User-Agent": "MatVerse-Agent/1.0"},
            )
            response.raise_for_status()
            data = response.json()
        results = [
            {
                "title": str(item.get("title", "")),
                "url": str(item.get("url", "")),
                "content": str(item.get("content", ""))[:1000],
                "engine": item.get("engine"),
            }
            for item in data.get("results", [])[:limit]
        ]
        return {"status": "PASS", "query": query, "results": results}

    def browser_snapshot(self, url: str, name: str) -> JSON:
        self._require_network()
        self._validate_url(url)
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            return {"status": "HOLD", "error": f"Install browser extras: {exc}"}
        target_dir = self.settings.workspace / "artifacts" / "browser"
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-") or "snapshot"
        screenshot = target_dir / f"{safe_name}.png"
        text_path = target_dir / f"{safe_name}.txt"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.goto(url, wait_until="networkidle", timeout=60_000)
            page.screenshot(path=str(screenshot), full_page=True)
            text_path.write_text(page.locator("body").inner_text(), encoding="utf-8")
            title = page.title()
            final_url = page.url
            browser.close()
        return {
            "status": "PASS",
            "title": title,
            "url": final_url,
            "screenshot": str(screenshot),
            "text": str(text_path),
        }

    def _create_website(self, name: str, title: str, sections: list[dict[str, str]]) -> JSON:
        return create_website(self.settings.workspace, name, title, sections)

    def _create_mobile_pwa(self, name: str, title: str, features: list[str]) -> JSON:
        return create_mobile_pwa(self.settings.workspace, name, title, features)

    def _create_slides(self, name: str, title: str, slides: list[dict[str, Any]]) -> JSON:
        return create_slides(self.settings.workspace, name, title, slides)

    def _create_video(self, name: str, scenes: list[dict[str, Any]]) -> JSON:
        return create_video(self.settings.workspace, name, scenes)

    def _require_network(self) -> None:
        if not self.settings.network_enabled:
            raise PermissionError("Network is disabled; set MATVERSE_NETWORK_ENABLED=1")

    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Only HTTP and HTTPS URLs are allowed")
        if parsed.hostname in {"169.254.169.254", "metadata.google.internal"}:
            raise PermissionError("Cloud metadata endpoints are blocked")
        try:
            addresses = {row[4][0] for row in socket.getaddrinfo(parsed.hostname, None)}
        except socket.gaierror as exc:
            raise ValueError(f"DNS resolution failed: {exc}") from exc
        if "169.254.169.254" in addresses:
            raise PermissionError("Cloud metadata endpoint is blocked")

    def _limit(self, value: str) -> str:
        maximum = self.settings.max_output_chars
        if len(value) <= maximum:
            return value
        half = maximum // 2
        return value[:half] + f"\n...<truncated {len(value) - maximum} chars>...\n" + value[-half:]
