from __future__ import annotations

from operator import add
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.agents.contracts import AgentResult, WorkflowState
from app.agents.specialists import (
    AGENT_REGISTRY,
    MANDATORY_AGENTS,
    SPECIALIST_TOOLS,
    run_document_agent,
    run_mcp_agent,
    run_rag_agent,
    run_recommendation_agent,
    run_risk_agent,
)
from app.core.config import Settings
from app.core.ids import new_id
from app.mcp.client import McpClient
from app.models.audit_event import AuditEvent
from app.models.enums import AuditEventType
from app.models.lease import Lease
from app.models.workflow import AgentExecution, PolicyEvaluation, WorkflowExecution
from app.policy.engine import (
    PolicyInput,
    evaluate_policy,
    lease_evidence_complete,
    lease_has_blocking_issues,
)
from app.policy.flags import effective_flags, flag_version
from app.rag.service import detect_amendment_conflicts
from app.services.time import utcnow


class GraphState(TypedDict):
    workflow_id: str
    lease_id: str
    results: Annotated[list[dict[str, Any]], add]
    policy: dict[str, Any] | None


def _skipped(name: str) -> AgentResult:
    return AgentResult(agent_name=name, execution_id=new_id(), status="SKIPPED", errors=["agent_disabled"])


def execute_workflow(
    db: Session,
    settings: Settings,
    lease: Lease,
    *,
    correlation_id: str,
    chunk_count: int,
) -> WorkflowState:
    flags = effective_flags(
        db, lease.organization_id, lease.property_id, kill_switch=settings.auto_approval_kill_switch
    )
    workflow = WorkflowExecution(
        id=new_id(),
        lease_id=lease.id,
        organization_id=lease.organization_id,
        property_id=lease.property_id,
        correlation_id=correlation_id,
        status="RUNNING",
        flag_version=flag_version(db, lease.organization_id, lease.property_id),
        created_at=utcnow(),
    )
    db.add(workflow)
    db.flush()
    client = McpClient(settings, db, workflow.id)

    def persist(result: AgentResult) -> AgentResult:
        db.add(
            AgentExecution(
                id=result.execution_id,
                workflow_id=workflow.id,
                agent_name=result.agent_name,
                status=result.status,
                findings=result.findings,
                evidence=result.evidence,
                errors=result.errors,
                duration_ms=result.duration_ms,
                created_at=utcnow(),
            )
        )
        return result

    def specialists(_: GraphState) -> dict[str, Any]:
        results: list[AgentResult] = []
        if flags.get("ENABLE_DOCUMENT_AGENT"):
            results.append(persist(run_document_agent(lease, chunk_count)))
        else:
            results.append(persist(_skipped("document")))
        if flags.get("ENABLE_LEASE_RAG_AGENT") and flags.get("ENABLE_RAG"):
            results.append(persist(run_rag_agent(db, lease, settings)))
        else:
            results.append(persist(_skipped("lease_rag")))

        def mcp_job(name: str) -> AgentResult:
            if not flags.get(AGENT_REGISTRY[name], False) or not flags.get("ENABLE_MCP_CONTEXT"):
                return persist(_skipped(name))
            server, tools = SPECIALIST_TOOLS[name]
            return persist(run_mcp_agent(name, server, tools, client, lease, correlation_id))

        names = ["property", "finance", "legal", "leasing"]
        if flags.get("ENABLE_INSURANCE_AGENT"):
            names.append("insurance")
        for name in names:
            results.append(mcp_job(name))
        return {"results": [item.model_dump() for item in results]}

    def risk(state: GraphState) -> dict[str, Any]:
        current = [AgentResult.model_validate(item) for item in state["results"]]
        if flags.get("ENABLE_RISK_AGENT"):
            result = persist(run_risk_agent(current))
        else:
            result = persist(_skipped("risk"))
        return {"results": [result.model_dump()]}

    def recommend(state: GraphState) -> dict[str, Any]:
        current = [AgentResult.model_validate(item) for item in state["results"]]
        if flags.get("ENABLE_AI_RECOMMENDATION") and flags.get("ENABLE_RECOMMENDATION_AGENT"):
            result = persist(run_recommendation_agent(current))
        else:
            result = persist(_skipped("recommendation"))
        return {"results": [result.model_dump()]}

    def policy_node(state: GraphState) -> dict[str, Any]:
        current = [AgentResult.model_validate(item) for item in state["results"]]
        by_name = {item.agent_name: item for item in current}
        required_disabled = any(not flags.get(AGENT_REGISTRY.get(name, ""), True) for name in MANDATORY_AGENTS)

        def _mandatory_ok(name: str) -> bool:
            result = by_name.get(name)
            if result is None:
                return False
            if name == "lease_rag":
                return result.status in {"SUCCESS", "INSUFFICIENT_EVIDENCE"}
            return result.status == "SUCCESS"

        mandatory_ok = all(_mandatory_ok(name) for name in MANDATORY_AGENTS)
        tools_ok = all(item.status != "FAILED" for item in current if item.agent_name in SPECIALIST_TOOLS)
        risk = by_name.get("risk")
        payload = PolicyInput(
            organization_id=lease.organization_id,
            property_id=lease.property_id,
            flags=flags,
            policy_version=settings.policy_version,
            lease_version=lease.version,
            expected_lease_version=lease.version,
            kill_switch=settings.auto_approval_kill_switch,
            mandatory_agents_ok=mandatory_ok,
            required_agent_disabled=required_disabled,
            required_tools_ok=tools_ok,
            evidence_complete=lease_evidence_complete(lease),
            has_blocking_issues=lease_has_blocking_issues(lease),
            has_amendment_conflict=bool(detect_amendment_conflicts(db, lease.organization_id, lease.property_id)),
            finance_threshold_exceeded=bool(risk.findings.get("finance_threshold_exceeded")) if risk else False,
            legal_exceptions=list(risk.findings.get("legal_exceptions") or []) if risk else [],
            leasing_complete=True,
            monthly_base_rent=lease.monthly_base_rent,
        )
        decision = evaluate_policy(payload)
        db.add(
            PolicyEvaluation(
                id=new_id(),
                workflow_id=workflow.id,
                lease_id=lease.id,
                lease_version=lease.version,
                policy_version=settings.policy_version,
                decision=decision.decision,
                reason_codes=decision.reason_codes,
                conditions=decision.conditions,
                dry_run=False,
                created_at=utcnow(),
            )
        )
        db.add(
            AuditEvent(
                id=new_id(),
                lease_id=lease.id,
                event_type=AuditEventType.POLICY_EVALUATED.value,
                actor="policy-engine",
                change_details={
                    "decision": decision.decision,
                    "reason_codes": decision.reason_codes,
                    "advisory_recommendation": True,
                    "authoritative": True,
                    "correlation_id": correlation_id,
                },
                occurred_at=utcnow(),
            )
        )
        return {"policy": decision.model_dump()}

    builder = StateGraph(GraphState)
    builder.add_node("specialists", specialists)
    builder.add_node("risk", risk)
    builder.add_node("recommend", recommend)
    builder.add_node("policy", policy_node)
    builder.add_edge(START, "specialists")
    builder.add_edge("specialists", "risk")
    builder.add_edge("risk", "recommend")
    builder.add_edge("recommend", "policy")
    builder.add_edge("policy", END)
    graph = builder.compile()
    raw = graph.invoke(
        {
            "workflow_id": workflow.id,
            "lease_id": lease.id,
            "results": [],
            "policy": None,
        }
    )
    results = [AgentResult.model_validate(item) for item in raw["results"]]
    workflow.status = "COMPLETED"
    workflow.completed_at = utcnow()
    workflow.policy_result = (raw.get("policy") or {}).get("decision")
    rec = next((item for item in results if item.agent_name == "recommendation"), None)
    workflow.recommendation = rec.findings if rec else None
    db.flush()
    return WorkflowState(
        lease_id=lease.id,
        organization_id=lease.organization_id,
        property_id=lease.property_id,
        correlation_id=correlation_id,
        flags=flags,
        results=results,
        policy=raw.get("policy"),
    )
