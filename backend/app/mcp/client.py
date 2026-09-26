from __future__ import annotations

import time
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.core.ids import new_id
from app.mcp.protocol import McpCallResult, McpTool, call_tool, list_tools
from app.models.workflow import McpToolCall
from app.services.time import utcnow

# Simulated unavailable servers for tests and fail-closed policy.
UNAVAILABLE_SERVERS: set[str] = set()


class McpClient:
    """In-process MCP client using official-style tool discovery and typed calls.

    Local demo transport is in-process JSON-RPC-equivalent invoke. Stdio server
    modules expose the same tool catalog for protocol-level tests.
    """

    def __init__(self, settings: Settings, db: Session | None = None, workflow_id: str | None = None) -> None:
        self.settings = settings
        self.db = db
        self.workflow_id = workflow_id

    def discover(self, server_name: str) -> list[McpTool]:
        if server_name in UNAVAILABLE_SERVERS:
            raise AppError("MCP_UNAVAILABLE", f"MCP server '{server_name}' is unavailable.", status_code=503)
        return list_tools(server_name)

    def invoke(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
        *,
        authorized_org: str,
        correlation_id: str,
    ) -> McpCallResult:
        started = time.perf_counter()
        status = "SUCCESS"
        payload: dict[str, Any] | None = None
        error = None
        try:
            if server_name in UNAVAILABLE_SERVERS:
                raise AppError("MCP_UNAVAILABLE", f"MCP server '{server_name}' is unavailable.", status_code=503)
            if arguments.get("organization_id") != authorized_org:
                raise AppError("MCP_UNAUTHORIZED", "Application authorization rejected the tool call.", 403)
            if time.perf_counter() - started > self.settings.mcp_timeout_seconds:
                raise AppError("MCP_TIMEOUT", "MCP tool timed out.", status_code=504)
            result = call_tool(server_name, tool_name, arguments)
            payload = result.content
            return result
        except AppError as exc:
            status = "FAILED"
            error = exc.message
            raise
        finally:
            duration = int((time.perf_counter() - started) * 1000)
            if self.db is not None and self.workflow_id:
                self.db.add(
                    McpToolCall(
                        id=new_id(),
                        workflow_id=self.workflow_id,
                        server_name=server_name,
                        tool_name=tool_name,
                        status=status,
                        request_payload=arguments,
                        response_payload=payload,
                        error=error,
                        duration_ms=duration,
                        correlation_id=correlation_id,
                        created_at=utcnow(),
                    )
                )
                self.db.flush()
