from __future__ import annotations

import json
from typing import Any

from app.mcp.catalog import TOOL_ALLOWLIST
from app.mcp.protocol import call_tool, list_tools


def build_server(server_name: str) -> Any:
    from mcp.server.fastmcp import FastMCP

    if server_name not in TOOL_ALLOWLIST:
        raise ValueError(f"Unknown MCP server '{server_name}'")
    server = FastMCP(server_name)

    def _register(tool_name: str) -> None:
        @server.tool(name=tool_name, description=f"{server_name} tool {tool_name}")
        def _tool(organization_id: str, property_id: str) -> str:
            result = call_tool(
                server_name,
                tool_name,
                {"organization_id": organization_id, "property_id": property_id},
            )
            return json.dumps(result.content)

    for name in sorted(TOOL_ALLOWLIST[server_name]):
        _register(name)
    return server


def discovered_tool_names(server_name: str) -> list[str]:
    return [tool.name for tool in list_tools(server_name)]
