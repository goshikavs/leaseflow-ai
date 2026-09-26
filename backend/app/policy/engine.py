from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.domain import PROPERTY_DALLAS, PROPERTY_LOGISTICS, PROPERTY_PROSPER
from app.models.enums import IssueSeverity
from app.models.lease import Lease

AUTO_APPROVED = "AUTO_APPROVED"
MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
ESCALATED = "ESCALATED"
BLOCKED = "BLOCKED"


class PolicyInput(BaseModel):
    organization_id: str
    property_id: str
    flags: dict[str, bool]
    policy_version: int
    lease_version: int
    expected_lease_version: int | None = None
    kill_switch: bool = False
    mandatory_agents_ok: bool = True
    required_agent_disabled: bool = False
    required_tools_ok: bool = True
    evidence_complete: bool = True
    has_blocking_issues: bool = False
    has_amendment_conflict: bool = False
    finance_threshold_exceeded: bool = False
    legal_exceptions: list[str] = Field(default_factory=list)
    leasing_complete: bool = True
    stale_context: bool = False
    monthly_base_rent: Decimal | None = None


class PolicyResult(BaseModel):
    decision: str
    reason_codes: list[str]
    conditions: dict[str, Any]


def evaluate_policy(payload: PolicyInput) -> PolicyResult:
    reasons: list[str] = []
    if payload.kill_switch or not payload.flags.get("ENABLE_AUTO_APPROVAL", False):
        reasons.append("AUTO_APPROVAL_DISABLED")
    if payload.flags.get("REQUIRE_MANUAL_APPROVAL"):
        reasons.append("MANUAL_ONLY_PROPERTY")
    if payload.property_id == PROPERTY_DALLAS:
        reasons.append("DALLAS_MANUAL_REVIEW")
    if payload.has_blocking_issues:
        reasons.append("BLOCKING_VALIDATION")
    if not payload.evidence_complete:
        reasons.append("INSUFFICIENT_EVIDENCE")
    if payload.has_amendment_conflict:
        reasons.append("AMENDMENT_CONFLICT")
    if payload.finance_threshold_exceeded:
        reasons.append("FINANCE_THRESHOLD")
    if payload.legal_exceptions:
        reasons.append("LEGAL_EXCEPTION")
    if not payload.leasing_complete:
        reasons.append("LEASING_INCOMPLETE")
    if not payload.mandatory_agents_ok:
        reasons.append("MANDATORY_AGENT_FAILED")
    if payload.required_agent_disabled:
        reasons.append("REQUIRED_AGENT_DISABLED")
    if not payload.required_tools_ok:
        reasons.append("MANDATORY_TOOL_FAILED")
    if payload.stale_context:
        reasons.append("STALE_CONTEXT")
    if payload.expected_lease_version is not None and payload.expected_lease_version != payload.lease_version:
        reasons.append("LEASE_VERSION_CHANGED")
    if payload.monthly_base_rent is None or payload.monthly_base_rent <= 0:
        reasons.append("INVALID_RENT")
    if payload.monthly_base_rent is not None and payload.monthly_base_rent > Decimal("5000.00"):
        reasons.append("RENT_ABOVE_AUTO_LIMIT")

    conditions = {
        "property_id": payload.property_id,
        "flags": payload.flags,
        "reason_codes": reasons,
        "policy_version": payload.policy_version,
    }

    if payload.property_id == PROPERTY_DALLAS or payload.flags.get("REQUIRE_MANUAL_APPROVAL"):
        return PolicyResult(decision=MANUAL_REVIEW_REQUIRED, reason_codes=sorted(set(reasons)), conditions=conditions)

    blocking = {
        "BLOCKING_VALIDATION",
        "INSUFFICIENT_EVIDENCE",
        "MANDATORY_AGENT_FAILED",
        "REQUIRED_AGENT_DISABLED",
        "MANDATORY_TOOL_FAILED",
        "STALE_CONTEXT",
        "LEASE_VERSION_CHANGED",
        "INVALID_RENT",
        "AUTO_APPROVAL_DISABLED",
    }
    if blocking.intersection(reasons):
        return PolicyResult(decision=BLOCKED, reason_codes=sorted(set(reasons)), conditions=conditions)

    escalate = {
        "AMENDMENT_CONFLICT",
        "LEGAL_EXCEPTION",
        "FINANCE_THRESHOLD",
        "RENT_ABOVE_AUTO_LIMIT",
        "LEASING_INCOMPLETE",
    }
    if payload.property_id == PROPERTY_LOGISTICS or escalate.intersection(reasons):
        return PolicyResult(decision=ESCALATED, reason_codes=sorted(set(reasons)), conditions=conditions)

    if payload.property_id == PROPERTY_PROSPER and not reasons:
        return PolicyResult(decision=AUTO_APPROVED, reason_codes=["PROSPER_POLICY_PASS"], conditions=conditions)

    return PolicyResult(
        decision=MANUAL_REVIEW_REQUIRED,
        reason_codes=sorted(set(reasons) or ["DEFAULT_REVIEW"]),
        conditions=conditions,
    )


def lease_evidence_complete(lease: Lease) -> bool:
    return all(
        [
            lease.tenant_name,
            lease.property_address,
            lease.commencement_date,
            lease.expiration_date,
            lease.monthly_base_rent and lease.monthly_base_rent > 0,
        ]
    )


def lease_has_blocking_issues(lease: Lease) -> bool:
    return any(
        issue.resolved_at is None and issue.severity == IssueSeverity.BLOCKING.value for issue in lease.issues
    )
