from typing import Any

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db_session, settings_dep
from app.core.config import Settings
from app.core.errors import AppError
from app.mcp.client import McpClient
from app.models.workflow import AgentExecution, McpToolCall, PolicyEvaluation, WorkflowExecution
from app.policy.engine import PolicyInput, evaluate_policy, lease_evidence_complete, lease_has_blocking_issues
from app.policy.flags import effective_flags, flag_version, seed_default_flags
from app.rag.service import detect_amendment_conflicts
from app.services.leases import get_lease

router = APIRouter(prefix="/api/v1", tags=["platform"])


class EffectiveFlagsResponse(BaseModel):
    organization_id: str
    property_id: str
    config_version: int
    flags: dict[str, bool]
    restricted: bool = True
    note: str = "Read-only effective configuration. Frontend flags are not authoritative."


class PolicyDryRunRequest(BaseModel):
    lease_id: str
    expected_lease_version: int | None = None


class WorkflowOut(BaseModel):
    id: str
    lease_id: str
    correlation_id: str
    status: str
    policy_result: str | None
    recommendation: dict[str, Any] | None
    flag_version: int
    agents: list[dict[str, Any]]
    tool_calls: list[dict[str, Any]]
    policy_evaluations: list[dict[str, Any]]


@router.get("/flags/effective", response_model=EffectiveFlagsResponse)
def get_effective_flags(
    organization_id: str,
    property_id: str,
    db: Session = Depends(db_session),
    settings: Settings = Depends(settings_dep),
    x_organization_id: str | None = Header(default=None),
) -> EffectiveFlagsResponse:
    requested = (x_organization_id or settings.default_organization_id).strip()
    if organization_id != requested:
        raise AppError("ORG_SCOPE_DENIED", "Cross-organization flag access is not permitted.", status_code=403)
    seed_default_flags(db)
    flags = effective_flags(db, organization_id, property_id, kill_switch=settings.auto_approval_kill_switch)
    return EffectiveFlagsResponse(
        organization_id=organization_id,
        property_id=property_id,
        config_version=flag_version(db, organization_id, property_id),
        flags=flags,
    )


@router.get("/leases/{lease_id}/workflow", response_model=WorkflowOut | None)
def get_workflow(
    lease_id: str,
    db: Session = Depends(db_session),
) -> WorkflowOut | None:
    get_lease(db, lease_id)
    workflow = db.scalar(
        select(WorkflowExecution)
        .where(WorkflowExecution.lease_id == lease_id)
        .order_by(WorkflowExecution.created_at.desc())
    )
    if workflow is None:
        return None
    agents = list(db.scalars(select(AgentExecution).where(AgentExecution.workflow_id == workflow.id)))
    tools = list(db.scalars(select(McpToolCall).where(McpToolCall.workflow_id == workflow.id)))
    policies = list(db.scalars(select(PolicyEvaluation).where(PolicyEvaluation.workflow_id == workflow.id)))
    return WorkflowOut(
        id=workflow.id,
        lease_id=workflow.lease_id,
        correlation_id=workflow.correlation_id,
        status=workflow.status,
        policy_result=workflow.policy_result,
        recommendation=workflow.recommendation,
        flag_version=workflow.flag_version,
        agents=[
            {
                "agent_name": item.agent_name,
                "status": item.status,
                "findings": item.findings,
                "errors": item.errors,
                "duration_ms": item.duration_ms,
            }
            for item in agents
        ],
        tool_calls=[
            {
                "server_name": item.server_name,
                "tool_name": item.tool_name,
                "status": item.status,
                "error": item.error,
                "duration_ms": item.duration_ms,
                "correlation_id": item.correlation_id,
            }
            for item in tools
        ],
        policy_evaluations=[
            {
                "decision": item.decision,
                "reason_codes": item.reason_codes,
                "conditions": item.conditions,
                "dry_run": item.dry_run,
                "policy_version": item.policy_version,
                "lease_version": item.lease_version,
            }
            for item in policies
        ],
    )


@router.post("/policy/evaluate")
def dry_run_policy(
    payload: PolicyDryRunRequest,
    db: Session = Depends(db_session),
    settings: Settings = Depends(settings_dep),
) -> dict[str, Any]:
    lease = get_lease(db, payload.lease_id)
    flags = effective_flags(
        db, lease.organization_id, lease.property_id, kill_switch=settings.auto_approval_kill_switch
    )
    result = evaluate_policy(
        PolicyInput(
            organization_id=lease.organization_id,
            property_id=lease.property_id,
            flags=flags,
            policy_version=settings.policy_version,
            lease_version=lease.version,
            expected_lease_version=payload.expected_lease_version,
            kill_switch=settings.auto_approval_kill_switch,
            evidence_complete=lease_evidence_complete(lease),
            has_blocking_issues=lease_has_blocking_issues(lease),
            has_amendment_conflict=bool(
                detect_amendment_conflicts(db, lease.organization_id, lease.property_id)
            ),
            monthly_base_rent=lease.monthly_base_rent,
        )
    )
    return {"dry_run": True, **result.model_dump()}


@router.get("/mcp/status")
def mcp_status(
    settings: Settings = Depends(settings_dep),
    db: Session = Depends(db_session),
) -> dict[str, Any]:
    client = McpClient(settings, db)
    servers = {}
    for name in ("property", "finance", "legal", "leasing", "insurance"):
        try:
            tools = [tool.name for tool in client.discover(name)]
            servers[name] = {"status": "available", "tools": tools}
        except Exception as exc:  # noqa: BLE001
            servers[name] = {"status": "unavailable", "error": str(exc), "tools": []}
    return {"transport": "in-process", "servers": servers}


@router.get("/leases/{lease_id}/audit-timeline")
def audit_timeline(
    lease_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(db_session),
) -> dict[str, Any]:
    lease = get_lease(db, lease_id)
    workflow = db.scalar(
        select(WorkflowExecution)
        .where(WorkflowExecution.lease_id == lease_id)
        .order_by(WorkflowExecution.created_at.desc())
    )
    events = sorted(lease.audit_events, key=lambda item: item.occurred_at)
    return {
        "lease_id": lease.id,
        "organization_id": lease.organization_id,
        "property_id": lease.property_id,
        "approval_source": lease.approval_source,
        "status": lease.status,
        "events": [
            {
                "id": event.id,
                "event_type": event.event_type,
                "actor": event.actor,
                "change_details": event.change_details,
                "occurred_at": event.occurred_at.isoformat(),
            }
            for event in events[-limit:]
        ],
        "latest_workflow_id": workflow.id if workflow else None,
        "latest_policy_result": workflow.policy_result if workflow else None,
    }
