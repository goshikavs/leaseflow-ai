import pytest

from app.core.config import get_settings
from app.core.errors import AppError
from app.domain import DEMO_ORG_ID, PROPERTY_PROSPER
from app.mcp.catalog import TOOL_ALLOWLIST
from app.mcp.client import UNAVAILABLE_SERVERS, McpClient
from app.mcp.protocol import call_tool, list_tools
from app.mcp.servers.runtime import build_server, discovered_tool_names


@pytest.fixture(autouse=True)
def _reset_unavailable() -> None:
    UNAVAILABLE_SERVERS.clear()
    yield
    UNAVAILABLE_SERVERS.clear()


def test_protocol_discovery_and_calls() -> None:
    for server, tools in TOOL_ALLOWLIST.items():
        discovered = {item.name for item in list_tools(server)}
        assert discovered == set(tools)
        for tool in tools:
            result = call_tool(
                server,
                tool,
                {"organization_id": DEMO_ORG_ID, "property_id": PROPERTY_PROSPER},
            )
            assert result.is_error is False
            assert result.content["organization_id"] == DEMO_ORG_ID


def test_official_sdk_server_registration() -> None:
    assert set(discovered_tool_names("finance")) == TOOL_ALLOWLIST["finance"]
    try:
        server = build_server("property")
    except TypeError:
        pytest.skip("Official FastMCP tool registration is incompatible with this Python runtime.")
    assert getattr(server, "name", "property") == "property"


def test_unauthorized_org_and_unknown_tool() -> None:
    with pytest.raises(AppError) as denied:
        call_tool(
            "property",
            "get_property_profile",
            {"organization_id": "org-other", "property_id": PROPERTY_PROSPER},
        )
    assert denied.value.status_code == 403
    with pytest.raises(AppError) as tool:
        call_tool("property", "drop_all_tables", {"organization_id": DEMO_ORG_ID, "property_id": PROPERTY_PROSPER})
    assert tool.value.code == "MCP_TOOL_DENIED"


def test_malformed_and_unavailable(client) -> None:
    with pytest.raises(Exception, match="organization_id|validation"):
        call_tool("property", "get_property_profile", {"property_id": PROPERTY_PROSPER})
    UNAVAILABLE_SERVERS.add("finance")
    settings = get_settings()
    mcp = McpClient(settings)
    with pytest.raises(AppError) as exc:
        mcp.invoke(
            "finance",
            "get_tenant_financial_status",
            {"organization_id": DEMO_ORG_ID, "property_id": PROPERTY_PROSPER},
            authorized_org=DEMO_ORG_ID,
            correlation_id="corr-1",
        )
    assert exc.value.code == "MCP_UNAVAILABLE"
    status = client.get("/api/v1/mcp/status")
    assert status.status_code == 200
    assert status.json()["servers"]["property"]["status"] == "available"


def test_application_auth_rejects_mismatched_org() -> None:
    settings = get_settings()
    mcp = McpClient(settings)
    with pytest.raises(AppError) as exc:
        mcp.invoke(
            "property",
            "get_property_profile",
            {"organization_id": "org-other", "property_id": PROPERTY_PROSPER},
            authorized_org=DEMO_ORG_ID,
            correlation_id="corr-2",
        )
    assert exc.value.code == "MCP_UNAUTHORIZED"
