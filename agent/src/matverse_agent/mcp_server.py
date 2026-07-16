from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import Settings
from .ledger import Ledger
from .tools import ToolRegistry


settings = Settings.from_env(os.getenv("MATVERSE_WORKSPACE", Path.cwd()))
ledger = Ledger(settings.database_path)
mcp = FastMCP(
    "MatVerse Agent Local",
    host=settings.host,
    port=settings.port,
    streamable_http_path="/mcp",
    json_response=True,
)


def _execute(tool_name: str, arguments: dict[str, Any]) -> str:
    run_id = f"mcp-{uuid.uuid4().hex}"
    ledger.start_run(run_id, f"MCP tool: {tool_name}")
    registry = ToolRegistry(settings, ledger, run_id)
    try:
        result = registry.execute(tool_name, arguments)
        status = "PASS" if result.get("status") == "PASS" else "BLOCK"
        ledger.finish_run(run_id, status)
    except Exception:
        ledger.finish_run(run_id, "BLOCK")
        raise
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def list_files(pattern: str = "**/*", limit: int = 500) -> str:
    """List files confined to the configured workspace."""
    return _execute("list_files", {"pattern": pattern, "limit": limit})


@mcp.tool()
def read_file(path: str, start_line: int = 1, end_line: int | None = None) -> str:
    """Read a UTF-8 workspace file with line bounds."""
    arguments: dict[str, Any] = {"path": path, "start_line": start_line}
    if end_line is not None:
        arguments["end_line"] = end_line
    return _execute("read_file", arguments)


@mcp.tool()
def write_file(path: str, content: str, overwrite: bool = False) -> str:
    """Write a UTF-8 file inside the workspace."""
    return _execute(
        "write_file",
        {"path": path, "content": content, "overwrite": overwrite},
    )


@mcp.tool()
def replace_text(path: str, old: str, new: str, count: int = 0) -> str:
    """Replace exact text in a workspace file."""
    return _execute(
        "replace_text",
        {"path": path, "old": old, "new": new, "count": count},
    )


@mcp.tool()
def search_text(query: str, glob: str = "**/*", max_results: int = 100) -> str:
    """Search text files inside the workspace."""
    return _execute(
        "search_text",
        {"query": query, "glob": glob, "max_results": max_results},
    )


@mcp.tool()
def run_command(command: str, timeout_seconds: int = 180) -> str:
    """Execute a governed shell command inside the workspace."""
    return _execute(
        "run_command",
        {"command": command, "timeout_seconds": timeout_seconds},
    )


@mcp.tool()
def web_search(query: str, limit: int = 10) -> str:
    """Search through the configured local SearXNG service."""
    return _execute("web_search", {"query": query, "limit": limit})


@mcp.tool()
def http_get(url: str, max_bytes: int = 1_000_000) -> str:
    """Fetch a governed HTTP resource when network access is enabled."""
    return _execute("http_get", {"url": url, "max_bytes": max_bytes})


@mcp.tool()
def create_website(name: str, title: str, sections_json: str) -> str:
    """Create a static website. sections_json must be a JSON array of heading/body objects."""
    sections = json.loads(sections_json)
    if not isinstance(sections, list):
        raise ValueError("sections_json must decode to an array")
    return _execute(
        "create_website",
        {"name": name, "title": title, "sections": sections},
    )


@mcp.tool()
def create_mobile_pwa(name: str, title: str, features_json: str) -> str:
    """Create an installable PWA. features_json must be a JSON string array."""
    features = json.loads(features_json)
    if not isinstance(features, list) or not all(isinstance(item, str) for item in features):
        raise ValueError("features_json must decode to a string array")
    return _execute(
        "create_mobile_pwa",
        {"name": name, "title": title, "features": features},
    )


@mcp.tool()
def create_slides(name: str, title: str, slides_json: str) -> str:
    """Create a PPTX. slides_json must be an array of title/bullets objects."""
    slides = json.loads(slides_json)
    if not isinstance(slides, list):
        raise ValueError("slides_json must decode to an array")
    return _execute(
        "create_slides",
        {"name": name, "title": title, "slides": slides},
    )


@mcp.tool()
def create_video(name: str, scenes_json: str) -> str:
    """Create an MP4. scenes_json must be an array of title/body/duration objects."""
    scenes = json.loads(scenes_json)
    if not isinstance(scenes, list):
        raise ValueError("scenes_json must decode to an array")
    return _execute("create_video", {"name": name, "scenes": scenes})


def main() -> None:
    mcp.run(transport="streamable-http")
