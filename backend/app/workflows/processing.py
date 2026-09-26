import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError, ConflictError
from app.core.ids import new_id
from app.extraction.evidence import verify_field
from app.extraction.pdf import parse_pdf
from app.extraction.providers.factory import get_extraction_provider
from app.models.audit_event import AuditEvent
from app.models.document import Document
from app.models.enums import (
    AuditEventType,
    ExtractionStatus,
    IssueSeverity,
    LeaseStatus,
    ProcessingStatus,
)
from app.models.extraction import Extraction
from app.models.field_evidence import FieldEvidence
from app.models.lease import Lease
from app.models.validation_issue import ValidationIssue
from app.services.mapping import lease_values_from_extraction
from app.services.time import utcnow
from app.services.validation import validate_lease_record

logger = logging.getLogger(__name__)


def process_document(db: Session, settings: Settings, document: Document, actor: str) -> Lease:
    if document.processing_status == ProcessingStatus.PROCESSING.value:
        raise ConflictError("This document is already being processed.")
    if (
        document.processing_status
        in {
            ProcessingStatus.AWAITING_REVIEW.value,
            ProcessingStatus.APPROVED.value,
        }
        and document.lease
    ):
        return document.lease

    document.processing_status = ProcessingStatus.PROCESSING.value
    document.processing_error = None
    db.flush()

    try:
        parsed = parse_pdf(Path(document.storage_path))
        provider = get_extraction_provider(settings)
        raw_result = provider.extract(parsed, document.content_hash, document.original_filename)
        verified_fields = {name: verify_field(field, parsed) for name, field in raw_result.field_map().items()}
        verified = raw_result.model_copy(update=verified_fields)

        extraction = Extraction(
            id=new_id(),
            document_id=document.id,
            provider=provider.name,
            model_name=provider.model_name,
            extraction_status=ExtractionStatus.SUCCEEDED.value,
            structured_output=raw_result.model_dump(),
            created_at=utcnow(),
        )
        db.add(extraction)
        db.flush()

        for name, field in verified.field_map().items():
            db.add(
                FieldEvidence(
                    id=new_id(),
                    extraction_id=extraction.id,
                    field_name=name,
                    page_number=field.page_number,
                    source_text=field.source_text,
                    extracted_value=field.value,
                    confidence_status=field.confidence_status,
                )
            )

        values = lease_values_from_extraction(verified)
        lease = document.lease
        now = utcnow()
        if lease is None:
            lease = Lease(
                id=new_id(),
                document_id=document.id,
                created_at=now,
                updated_at=now,
                version=1,
                status=LeaseStatus.AWAITING_REVIEW.value,
                **values,
            )
            db.add(lease)
        else:
            for key, value in values.items():
                setattr(lease, key, value)
            lease.status = LeaseStatus.AWAITING_REVIEW.value
            lease.updated_at = now
            lease.version += 1
        db.flush()

        _replace_open_issues(db, lease)
        db.add(
            AuditEvent(
                id=new_id(),
                lease_id=lease.id,
                event_type=AuditEventType.PROCESSING_COMPLETED.value,
                actor=actor,
                change_details={
                    "provider": provider.name,
                    "fixture_mode": provider.is_fixture,
                    "extraction_id": extraction.id,
                },
                occurred_at=now,
            )
        )
        document.processing_status = ProcessingStatus.AWAITING_REVIEW.value
        document.processing_error = None
        db.commit()
        db.refresh(lease)
        return lease
    except AppError as exc:
        db.rollback()
        _mark_failed(db, document, actor, exc.message)
        raise
    except Exception:
        db.rollback()
        logger.exception("Document processing failed", extra={"document_id": document.id})
        _mark_failed(db, document, actor, "Document processing failed.")
        raise AppError("PROCESSING_FAILED", "Document processing failed.", status_code=500) from None


def _replace_open_issues(db: Session, lease: Lease) -> list[ValidationIssue]:
    now = utcnow()
    for issue in list(lease.issues):
        if issue.resolved_at is None:
            issue.resolved_at = now
    created: list[ValidationIssue] = []
    for draft in validate_lease_record(lease):
        issue = ValidationIssue(
            id=new_id(),
            lease_id=lease.id,
            field_name=draft.field_name,
            issue_code=draft.issue_code,
            severity=draft.severity.value,
            description=draft.description,
            resolved_at=None,
        )
        db.add(issue)
        lease.issues.append(issue)
        created.append(issue)
    db.flush()
    return created


def replace_validation_issues(db: Session, lease: Lease) -> list[ValidationIssue]:
    created = _replace_open_issues(db, lease)
    return created


def blocking_issues(lease: Lease) -> list[ValidationIssue]:
    return [
        issue for issue in lease.issues if issue.resolved_at is None and issue.severity == IssueSeverity.BLOCKING.value
    ]


def _mark_failed(db: Session, document: Document, actor: str, message: str) -> None:
    session_document = db.get(Document, document.id)
    if session_document is None:
        return
    session_document.processing_status = ProcessingStatus.FAILED.value
    session_document.processing_error = message
    if session_document.lease:
        db.add(
            AuditEvent(
                id=new_id(),
                lease_id=session_document.lease.id,
                event_type=AuditEventType.PROCESSING_FAILED.value,
                actor=actor,
                change_details={"reason": message},
                occurred_at=utcnow(),
            )
        )
    db.commit()
