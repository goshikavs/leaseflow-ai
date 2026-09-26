from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from app.agents.contracts import AgentResult
from app.core.config import Settings
from app.core.ids import new_id
from app.mcp.client import McpClient
from app.models.lease import Lease
from app.rag.service import detect_amendment_conflicts, search_chunks


def _timed(name: str, fn: Callable[[], dict[str, Any]]) -> AgentResult:
    started = time.perf_counter()
    try:
        payload = fn()
        status = payload.pop("status", "SUCCESS")
        return AgentResult(
            agent_name=name,
            execution_id=new_id(),
            status=status,
            findings=payload.get("findings", {}),
            evidence=payload.get("evidence", []),
            source_versions=payload.get("source_versions", {}),
            errors=payload.get("errors", []),
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
    except Exception as exc:  # noqa: BLE001 - specialist boundary
        return AgentResult(
            agent_name=name,
            execution_id=new_id(),
            status="FAILED",
            errors=[str(exc)],
            duration_ms=int((time.perf_counter() - started) * 1000),
        )


def run_document_agent(lease: Lease, chunk_count: int) -> AgentResult:
    return _timed(
        "document",
        lambda: {
            "findings": {
                "document_id": lease.document_id,
                "indexed_chunks": chunk_count,
                "filename": lease.document.original_filename if lease.document else None,
            }
        },
    )


def run_rag_agent(db: Session, lease: Lease, settings: Settings) -> AgentResult:
    def _run() -> dict[str, Any]:
        chunks = search_chunks(
            db,
            "rent renewal notice commencement expiration amendment",
            organization_id=lease.organization_id,
            property_ids=[lease.property_id],
            lease_id=lease.id,
            min_score=min(settings.rag_min_score, 0.05),
        )
        conflicts = detect_amendment_conflicts(db, lease.organization_id, lease.property_id)
        status = "INSUFFICIENT_EVIDENCE" if not chunks else "SUCCESS"
        return {
            "status": status,
            "findings": {"chunk_count": len(chunks), "conflicts": conflicts},
            "evidence": [item.model_dump() for item in chunks],
        }

    return _timed("lease_rag", _run)


def run_mcp_agent(
    name: str,
    server: str,
    tools: list[str],
    client: McpClient,
    lease: Lease,
    correlation_id: str,
) -> AgentResult:
    def _run() -> dict[str, Any]:
        findings: dict[str, Any] = {"tools": []}
        for tool in tools:
            result = client.invoke(
                server,
                tool,
                {"organization_id": lease.organization_id, "property_id": lease.property_id},
                authorized_org=lease.organization_id,
                correlation_id=correlation_id,
            )
            findings["tools"].append({"tool": tool, "content": result.content})
        return {"findings": findings}

    return _timed(name, _run)


def run_risk_agent(results: list[AgentResult]) -> AgentResult:
    def _run() -> dict[str, Any]:
        missing = [item.agent_name for item in results if item.status in {"FAILED", "TIMED_OUT"}]
        insufficient = [item.agent_name for item in results if item.status == "INSUFFICIENT_EVIDENCE"]
        conflicts = []
        for item in results:
            conflicts.extend(item.findings.get("conflicts", []) if isinstance(item.findings, dict) else [])
        legal = next((item for item in results if item.agent_name == "legal"), None)
        finance = next((item for item in results if item.agent_name == "finance"), None)
        legal_exceptions = []
        finance_exceeded = False
        if legal and legal.findings.get("tools"):
            legal_exceptions = legal.findings["tools"][0]["content"].get("unresolved_exceptions", [])
        if finance and finance.findings.get("tools"):
            finance_exceeded = bool(finance.findings["tools"][0]["content"].get("threshold_exceeded"))
        return {
            "findings": {
                "failed_agents": missing,
                "insufficient_agents": insufficient,
                "conflicts": conflicts,
                "legal_exceptions": legal_exceptions,
                "finance_threshold_exceeded": finance_exceeded,
            }
        }

    return _timed("risk", _run)


def run_recommendation_agent(results: list[AgentResult]) -> AgentResult:
    def _run() -> dict[str, Any]:
        risk = next((item for item in results if item.agent_name == "risk"), None)
        failed = (risk.findings.get("failed_agents") if risk else []) or []
        conflicts = (risk.findings.get("conflicts") if risk else []) or []
        recommendation = "manual_review"
        if not failed and not conflicts:
            recommendation = "eligible_for_policy_evaluation"
        return {
            "findings": {
                "recommendation": recommendation,
                "advisory_only": True,
                "summary": "Advisory recommendation only. The policy engine is authoritative.",
            }
        }

    return _timed("recommendation", _run)


SPECIALIST_TOOLS = {
    "property": ("property", ["get_property_profile", "get_property_maintenance_status"]),
    "finance": ("finance", ["get_tenant_financial_status", "get_property_financial_thresholds"]),
    "legal": ("legal", ["get_legal_review_status", "get_approved_clause_templates"]),
    "leasing": ("leasing", ["get_leasing_context", "get_lease_negotiation_status"]),
    "insurance": ("insurance", ["get_insurance_compliance"]),
}

AGENT_REGISTRY = {
    "document": "ENABLE_DOCUMENT_AGENT",
    "lease_rag": "ENABLE_LEASE_RAG_AGENT",
    "property": "ENABLE_PROPERTY_AGENT",
    "finance": "ENABLE_FINANCE_AGENT",
    "legal": "ENABLE_LEGAL_AGENT",
    "leasing": "ENABLE_LEASING_AGENT",
    "insurance": "ENABLE_INSURANCE_AGENT",
    "risk": "ENABLE_RISK_AGENT",
    "recommendation": "ENABLE_RECOMMENDATION_AGENT",
}

MANDATORY_AGENTS = {"document", "lease_rag", "property", "finance", "legal", "leasing", "risk"}
