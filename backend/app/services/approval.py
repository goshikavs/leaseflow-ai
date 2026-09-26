"""Single approval write-path used by human review and policy-controlled auto-approval."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import ValidationAppError
from app.core.ids import new_id
from app.models.audit_event import AuditEvent
from app.models.enums import AuditEventType, IssueSeverity, LeaseStatus, ProcessingStatus
from app.models.lease import Lease
from app.services.time import utcnow
from app.workflows.processing import replace_validation_issues

HUMAN_REVIEW = "HUMAN_REVIEW"


def apply_approval(
    db: Session,
    lease: Lease,
    actor: str,
    *,
    approval_source: str,
    extra_details: dict[str, Any] | None = None,
) -> None:
    """Commit an approved lease status using the original validation and audit rules.

    Agents and the policy engine must call this helper. They do not write lease.status
    themselves. Extraction output remains in extractions/field_evidence.
    """
    created_issues = replace_validation_issues(db, lease)
    open_blocking = [issue for issue in created_issues if issue.severity == IssueSeverity.BLOCKING.value]
    if open_blocking:
        raise ValidationAppError(
            "Blocking validation issues must be resolved before approval.",
            code="BLOCKING_ISSUES",
            details=[
                {"field": issue.field_name, "code": issue.issue_code, "description": issue.description}
                for issue in open_blocking
            ],
        )

    lease.status = LeaseStatus.APPROVED.value
    lease.approved_by = actor
    lease.approved_at = utcnow()
    lease.updated_at = utcnow()
    lease.version += 1
    lease.approval_source = approval_source
    if lease.document:
        lease.document.processing_status = ProcessingStatus.APPROVED.value
    details = {"reviewed_by": actor, "approval_source": approval_source}
    if extra_details:
        details.update(extra_details)
    db.add(
        AuditEvent(
            id=new_id(),
            lease_id=lease.id,
            event_type=AuditEventType.LEASE_APPROVED.value,
            actor=actor,
            change_details=details,
            occurred_at=utcnow(),
        )
    )
