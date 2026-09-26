from decimal import Decimal

from app.agents.contracts import AgentResult
from app.agents.specialists import AGENT_REGISTRY, run_recommendation_agent, run_risk_agent
from app.core.ids import new_id
from app.domain import PROPERTY_PROSPER
from app.policy.engine import AUTO_APPROVED, BLOCKED, MANUAL_REVIEW_REQUIRED, PolicyInput, evaluate_policy


def _result(name: str, status: str = "SUCCESS", findings: dict | None = None) -> AgentResult:
    return AgentResult(agent_name=name, execution_id=new_id(), status=status, findings=findings or {})


def test_registry_supports_optional_insurance_without_renaming_others() -> None:
    assert "insurance" in AGENT_REGISTRY
    assert AGENT_REGISTRY["finance"] == "ENABLE_FINANCE_AGENT"
    assert "document" in AGENT_REGISTRY


def test_risk_aggregates_failures_and_conflicts() -> None:
    results = [
        _result("legal", findings={"tools": [{"content": {"unresolved_exceptions": ["lien"]}}]}),
        _result("finance", findings={"tools": [{"content": {"threshold_exceeded": True}}]}),
        _result("lease_rag", findings={"conflicts": [{"section": "rent"}]}),
        _result("property", status="FAILED"),
    ]
    risk = run_risk_agent(results)
    assert risk.status == "SUCCESS"
    assert "property" in risk.findings["failed_agents"]
    assert risk.findings["finance_threshold_exceeded"] is True
    assert risk.findings["legal_exceptions"] == ["lien"]
    rec = run_recommendation_agent([*results, risk])
    assert rec.findings["advisory_only"] is True
    assert rec.findings["recommendation"] == "manual_review"


def test_disabled_required_agent_blocks_auto_approval() -> None:
    flags = {key: True for key in (
        "ENABLE_AUTO_APPROVAL",
        "REQUIRE_MANUAL_APPROVAL",
    )}
    flags["REQUIRE_MANUAL_APPROVAL"] = False
    result = evaluate_policy(
        PolicyInput(
            organization_id="org-harborpoint",
            property_id=PROPERTY_PROSPER,
            flags=flags,
            policy_version=1,
            lease_version=1,
            required_agent_disabled=True,
            monthly_base_rent=Decimal("4200.00"),
        )
    )
    assert result.decision == BLOCKED
    assert "REQUIRED_AGENT_DISABLED" in result.reason_codes


def test_supervisor_runs_for_prosper(client) -> None:
    from pathlib import Path

    from tests.helpers import process_pdf

    path = Path(__file__).resolve().parents[2] / "samples" / "prosper_retail_lease.pdf"
    processed = process_pdf(client, path, organization_id="org-harborpoint", property_id="prop-prosper-retail")
    workflow = client.get(f"/api/v1/leases/{processed['lease_id']}/workflow")
    assert workflow.status_code == 200
    body = workflow.json()
    names = {item["agent_name"] for item in body["agents"]}
    assert {"document", "lease_rag", "property", "finance", "legal", "leasing", "risk", "recommendation"} <= names
    assert body["policy_result"] in {AUTO_APPROVED, MANUAL_REVIEW_REQUIRED, BLOCKED}
    insurance = next((item for item in body["agents"] if item["agent_name"] == "insurance"), None)
    assert insurance is None or insurance["status"] == "SKIPPED"
