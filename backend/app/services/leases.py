import hashlib
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.core.ids import new_id
from app.integrations.contract import build_export_payload
from app.models.audit_event import AuditEvent
from app.models.document import Document
from app.models.enums import AuditEventType, IssueSeverity, LeaseStatus, ProcessingStatus
from app.models.export_event import ExportEvent
from app.models.extraction import Extraction
from app.models.lease import Lease
from app.schemas.export import ApprovedLeaseExport
from app.schemas.lease import (
    ApproveRequest,
    AuditEventOut,
    FieldEvidenceOut,
    LeaseDetail,
    LeaseSummary,
    LeaseUpdate,
    ValidationIssueOut,
)
from app.services.time import utcnow
from app.workflows.processing import replace_validation_issues


def get_lease(db: Session, lease_id: str) -> Lease:
    lease = db.scalar(
        select(Lease)
        .options(
            selectinload(Lease.document).selectinload(Document.extractions).selectinload(Extraction.evidence),
            selectinload(Lease.issues),
            selectinload(Lease.audit_events),
        )
        .where(Lease.id == lease_id)
    )
    if lease is None:
        raise NotFoundError("Lease not found.")
    return lease


def list_leases(db: Session, page: int, page_size: int, status: str | None) -> tuple[list[Lease], int]:
    query = select(Lease).options(selectinload(Lease.document), selectinload(Lease.issues))
    count_query = select(func.count()).select_from(Lease)
    if status:
        query = query.where(Lease.status == status)
        count_query = count_query.where(Lease.status == status)
    total = db.scalar(count_query) or 0
    items = list(db.scalars(query.order_by(Lease.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)))
    return items, total


def latest_extraction(lease: Lease) -> Extraction | None:
    if not lease.document or not lease.document.extractions:
        return None
    return sorted(lease.document.extractions, key=lambda item: item.created_at, reverse=True)[0]


def to_summary(lease: Lease) -> LeaseSummary:
    blocking = sum(
        1 for issue in lease.issues if issue.resolved_at is None and issue.severity == IssueSeverity.BLOCKING.value
    )
    return LeaseSummary(
        id=lease.id,
        document_id=lease.document_id,
        original_filename=lease.document.original_filename if lease.document else None,
        tenant_name=lease.tenant_name,
        landlord_name=lease.landlord_name,
        property_address=lease.property_address,
        status=lease.status,
        version=lease.version,
        created_at=lease.created_at,
        updated_at=lease.updated_at,
        blocking_issue_count=blocking,
    )


def to_detail(lease: Lease, fixture_mode: bool) -> LeaseDetail:
    extraction = latest_extraction(lease)
    evidence = []
    if extraction:
        evidence = [
            FieldEvidenceOut(
                field_name=item.field_name,
                page_number=item.page_number,
                source_text=item.source_text,
                extracted_value=item.extracted_value,
                confidence_status=item.confidence_status,
            )
            for item in extraction.evidence
        ]
    return LeaseDetail(
        id=lease.id,
        document_id=lease.document_id,
        original_filename=lease.document.original_filename if lease.document else None,
        processing_status=lease.document.processing_status if lease.document else None,
        tenant_name=lease.tenant_name,
        landlord_name=lease.landlord_name,
        property_address=lease.property_address,
        commencement_date=lease.commencement_date,
        expiration_date=lease.expiration_date,
        monthly_base_rent=lease.monthly_base_rent,
        currency=lease.currency,
        renewal_notice_days=lease.renewal_notice_days,
        status=lease.status,
        version=lease.version,
        created_at=lease.created_at,
        updated_at=lease.updated_at,
        approved_by=lease.approved_by,
        approved_at=lease.approved_at,
        extraction_provider=extraction.provider if extraction else None,
        fixture_mode=fixture_mode and (extraction.provider == "fixture" if extraction else fixture_mode),
        evidence=evidence,
        issues=[
            ValidationIssueOut(
                id=issue.id,
                field_name=issue.field_name,
                issue_code=issue.issue_code,
                severity=issue.severity,
                description=issue.description,
                resolved_at=issue.resolved_at,
            )
            for issue in sorted(lease.issues, key=lambda item: (item.resolved_at is not None, item.severity))
        ],
    )


def update_lease(db: Session, lease: Lease, payload: LeaseUpdate, actor: str) -> Lease:
    if lease.status == LeaseStatus.APPROVED.value:
        raise ConflictError("Approved leases cannot be edited.")
    if payload.version != lease.version:
        raise ConflictError("The lease was updated by another request. Refresh and retry.", code="VERSION_CONFLICT")

    changes: dict[str, dict[str, str | None]] = {}
    fields = [
        "tenant_name",
        "landlord_name",
        "property_address",
        "commencement_date",
        "expiration_date",
        "monthly_base_rent",
        "currency",
        "renewal_notice_days",
    ]
    for field in fields:
        new_value = getattr(payload, field)
        old_value = getattr(lease, field)
        if field in payload.model_fields_set and new_value != old_value:
            changes[field] = {"from": _stringify(old_value), "to": _stringify(new_value)}
            setattr(lease, field, new_value)

    lease.version += 1
    lease.updated_at = utcnow()
    lease.status = LeaseStatus.AWAITING_REVIEW.value
    replace_validation_issues(db, lease)
    db.add(
        AuditEvent(
            id=new_id(),
            lease_id=lease.id,
            event_type=AuditEventType.LEASE_CORRECTED.value,
            actor=actor,
            change_details=changes,
            occurred_at=utcnow(),
        )
    )
    db.commit()
    db.refresh(lease)
    return get_lease(db, lease.id)


def approve_lease(db: Session, lease: Lease, payload: ApproveRequest, default_actor: str) -> Lease:
    if lease.status == LeaseStatus.APPROVED.value:
        raise ConflictError("This lease is already approved.")
    if payload.version != lease.version:
        raise ConflictError("The lease was updated by another request. Refresh and retry.", code="VERSION_CONFLICT")

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

    actor = (payload.reviewed_by or default_actor).strip() or default_actor
    lease.status = LeaseStatus.APPROVED.value
    lease.approved_by = actor
    lease.approved_at = utcnow()
    lease.updated_at = utcnow()
    lease.version += 1
    if lease.document:
        lease.document.processing_status = ProcessingStatus.APPROVED.value
    db.add(
        AuditEvent(
            id=new_id(),
            lease_id=lease.id,
            event_type=AuditEventType.LEASE_APPROVED.value,
            actor=actor,
            change_details={"reviewed_by": actor},
            occurred_at=utcnow(),
        )
    )
    db.commit()
    db.refresh(lease)
    return get_lease(db, lease.id)


def export_lease(db: Session, lease: Lease, actor: str) -> ApprovedLeaseExport:
    if lease.status != LeaseStatus.APPROVED.value:
        raise ConflictError("Only approved leases can be exported.")
    payload = build_export_payload(lease)
    payload_hash = hashlib.sha256(payload.model_dump_json().encode("utf-8")).hexdigest()
    db.add(
        ExportEvent(
            id=new_id(),
            lease_id=lease.id,
            schema_version=payload.schema_version,
            payload_hash=payload_hash,
            exported_at=utcnow(),
        )
    )
    db.add(
        AuditEvent(
            id=new_id(),
            lease_id=lease.id,
            event_type=AuditEventType.LEASE_EXPORTED.value,
            actor=actor,
            change_details={"schema_version": payload.schema_version, "payload_hash": payload_hash},
            occurred_at=utcnow(),
        )
    )
    db.commit()
    return payload


def list_audit_events(lease: Lease) -> list[AuditEventOut]:
    events = sorted(lease.audit_events, key=lambda item: item.occurred_at)
    return [
        AuditEventOut(
            id=event.id,
            event_type=event.event_type,
            actor=event.actor,
            change_details=event.change_details,
            occurred_at=event.occurred_at,
        )
        for event in events
    ]


def _stringify(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return str(value)
