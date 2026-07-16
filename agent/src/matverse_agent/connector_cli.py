from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import Settings
from .connectors import MCPConnectorClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="matverse-connectors",
        description="List and call configured MCP connectors.",
    )
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list")

    tools = subparsers.add_parser("tools")
    tools.add_argument("connector")

    call = subparsers.add_parser("call")
    call.add_argument("connector")
    call.add_argument("tool")
    call.add_argument("arguments_json")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = Settings.from_env(args.workspace)
    if not settings.network_enabled:
        print("BLOCK: set MATVERSE_NETWORK_ENABLED=1 to use MCP connectors", file=sys.stderr)
        raise SystemExit(1)
    client = MCPConnectorClient(settings.workspace)
    try:
        if args.command == "list":
            result = client.list_connectors()
        elif args.command == "tools":
            result = client.list_tools(args.connector)
        else:
            arguments = json.loads(args.arguments_json)
            if not isinstance(arguments, dict):
                raise ValueError("arguments_json must decode to an object")
            result = client.call_tool(args.connector, args.tool, arguments)
    except Exception as exc:
        print(f"BLOCK: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))
