"""Keep MCP catalog processes visible in Compose and verify tool discovery."""

from __future__ import annotations

import time

from app.mcp.catalog import TOOL_ALLOWLIST
from app.mcp.protocol import list_tools
from app.mcp.servers.runtime import build_server


def verify() -> dict[str, list[str]]:
    discovered: dict[str, list[str]] = {}
    for name in TOOL_ALLOWLIST:
        build_server(name)
        discovered[name] = [tool.name for tool in list_tools(name)]
    return discovered


if __name__ == "__main__":
    print(verify())
    while True:
        time.sleep(60)
