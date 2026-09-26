from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.core.errors import AppError, NotFoundError
from app.mcp.catalog import CATALOG, TOOL_ALLOWLIST


class McpTool(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class McpCallResult(BaseModel):
    server_name: str
    tool_name: str
    content: dict[str, Any]
    is_error: bool = False


class ScopedRequest(BaseModel):
    organization_id: str
    property_id: str
    extra: dict[str, Any] = Field(default_factory=dict)


def list_tools(server_name: str) -> list[McpTool]:
    if server_name not in TOOL_ALLOWLIST:
        raise NotFoundError(f"Unknown MCP server '{server_name}'.")
    return [
        McpTool(
            name=name,
            description=f"{server_name} tool {name}",
            input_schema={
                "type": "object",
                "required": ["organization_id", "property_id"],
                "properties": {
                    "organization_id": {"type": "string"},
                    "property_id": {"type": "string"},
                },
            },
        )
        for name in sorted(TOOL_ALLOWLIST[server_name])
    ]


def call_tool(server_name: str, tool_name: str, arguments: dict[str, Any]) -> McpCallResult:
    if server_name not in TOOL_ALLOWLIST:
        raise NotFoundError(f"Unknown MCP server '{server_name}'.")
    if tool_name not in TOOL_ALLOWLIST[server_name]:
        raise AppError("MCP_TOOL_DENIED", f"Tool '{tool_name}' is not allowlisted.", status_code=403)
    scoped = ScopedRequest.model_validate(arguments)
    records = CATALOG.get(server_name, {})
    record = records.get(scoped.property_id)
    if record is None or record.get("organization_id") != scoped.organization_id:
        raise AppError("MCP_UNAUTHORIZED", "Organization cannot access this property record.", status_code=403)
    return McpCallResult(server_name=server_name, tool_name=tool_name, content=record)
