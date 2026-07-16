from __future__ import annotations

import asyncio
import json
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


@dataclass(frozen=True, slots=True)
class Connector:
    name: str
    url: str
    enabled: bool = True


class ConnectorConfig:
    def __init__(self, workspace: Path) -> None:
        self.path = workspace / ".matverse" / "connectors.json"

    def load(self) -> dict[str, Connector]:
        if not self.path.exists():
            return {}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        raw_connectors = data.get("connectors", {})
        if not isinstance(raw_connectors, dict):
            raise ValueError("connectors must be an object")
        result: dict[str, Connector] = {}
        for name, value in raw_connectors.items():
            if not isinstance(name, str) or not isinstance(value, dict):
                raise ValueError("Invalid connector entry")
            url = value.get("url")
            if not isinstance(url, str):
                raise ValueError(f"Connector {name!r} has no URL")
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError(f"Connector {name!r} URL must be HTTP(S)")
            result[name] = Connector(
                name=name,
                url=url,
                enabled=bool(value.get("enabled", True)),
            )
        return result

    def get(self, name: str) -> Connector:
        connector = self.load().get(name)
        if connector is None:
            raise KeyError(f"Unknown connector: {name}")
        if not connector.enabled:
            raise PermissionError(f"Connector is disabled: {name}")
        return connector


class MCPConnectorClient:
    def __init__(self, workspace: Path) -> None:
        self.config = ConnectorConfig(workspace)

    def list_connectors(self) -> list[dict[str, Any]]:
        return [
            {"name": item.name, "url": item.url, "enabled": item.enabled}
            for item in self.config.load().values()
        ]

    def list_tools(self, connector_name: str) -> list[dict[str, Any]]:
        connector = self.config.get(connector_name)
        return asyncio.run(self._list_tools(connector))

    def call_tool(
        self,
        connector_name: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        connector = self.config.get(connector_name)
        return asyncio.run(self._call_tool(connector, tool_name, arguments))

    @staticmethod
    async def _list_tools(connector: Connector) -> list[dict[str, Any]]:
        async with streamable_http_client(connector.url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    for tool in response.tools
                ]

    @staticmethod
    async def _call_tool(
        connector: Connector,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        async with streamable_http_client(connector.url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                available = await session.list_tools()
                names = {tool.name for tool in available.tools}
                if tool_name not in names:
                    raise KeyError(f"Tool {tool_name!r} is not exposed by {connector.name!r}")
                result = await session.call_tool(tool_name, arguments=arguments)
                return {
                    "is_error": bool(result.isError),
                    "content": [
                        item.model_dump(mode="json")
                        if hasattr(item, "model_dump")
                        else str(item)
                        for item in result.content
                    ],
                    "structured_content": result.structuredContent,
                }
