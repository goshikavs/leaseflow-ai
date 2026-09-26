from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import NotFoundError
from app.core.ids import new_id
from app.extraction.pdf import validate_pdf_bytes
from app.models.document import Document
from app.models.enums import LeaseStatus, ProcessingStatus
from app.models.lease import Lease
from app.schemas.document import DocumentSummary, StatsResponse
from app.services.storage import content_hash, safe_original_name, write_document
from app.services.time import utcnow


def create_document(
    db: Session,
    settings: Settings,
    filename: str,
    data: bytes,
    *,
    organization_id: str | None = None,
    property_id: str | None = None,
    document_type: str = "lease",
    document_version: int = 1,
    sample_key: str | None = None,
) -> Document:
    validate_pdf_bytes(data, filename, settings.max_upload_bytes)
    digest = content_hash(data)
    stored_path = write_document(settings.resolved_storage_dir, data)
    document = Document(
        id=new_id(),
        original_filename=safe_original_name(filename),
        storage_path=str(stored_path),
        content_hash=digest,
        uploaded_at=utcnow(),
        processing_status=ProcessingStatus.UPLOADED.value,
        organization_id=organization_id or settings.default_organization_id,
        property_id=property_id or "prop-unassigned",
        document_type=document_type,
        document_version=document_version,
        sample_key=sample_key,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_document(db: Session, document_id: str) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise NotFoundError("Document not found.")
    return document


def list_documents(db: Session, page: int, page_size: int) -> tuple[list[Document], int]:
    total = db.scalar(select(func.count()).select_from(Document)) or 0
    items = list(
        db.scalars(
            select(Document).order_by(Document.uploaded_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
    )
    return items, total


def document_summary(document: Document) -> DocumentSummary:
    return DocumentSummary(
        id=document.id,
        original_filename=document.original_filename,
        content_hash=document.content_hash,
        uploaded_at=document.uploaded_at,
        processing_status=document.processing_status,
        processing_error=document.processing_error,
        lease_id=document.lease.id if document.lease else None,
        organization_id=document.organization_id,
        property_id=document.property_id,
        document_type=document.document_type,
    )


def dashboard_stats(db: Session) -> StatsResponse:
    total_documents = db.scalar(select(func.count()).select_from(Document)) or 0
    awaiting_review = (
        db.scalar(select(func.count()).select_from(Lease).where(Lease.status == LeaseStatus.AWAITING_REVIEW.value)) or 0
    )
    approved_leases = (
        db.scalar(select(func.count()).select_from(Lease).where(Lease.status == LeaseStatus.APPROVED.value)) or 0
    )
    processing_errors = (
        db.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.processing_status == ProcessingStatus.FAILED.value)
        )
        or 0
    )
    return StatsResponse(
        total_documents=total_documents,
        awaiting_review=awaiting_review,
        approved_leases=approved_leases,
        processing_errors=processing_errors,
    )


def load_sample_bytes(settings: Settings, sample_key: str) -> tuple[str, bytes]:
    samples = {
        "sample_lease": "sample_lease.pdf",
        "missing_fields_lease": "missing_fields_lease.pdf",
        "conflicting_dates_lease": "conflicting_dates_lease.pdf",
        "prosper_retail_lease": "prosper_retail_lease.pdf",
        "dallas_plaza_lease": "dallas_plaza_lease.pdf",
        "logistics_park_lease": "logistics_park_lease.pdf",
        "logistics_park_large": "logistics_park_large.pdf",
        "logistics_park_amendment": "logistics_park_amendment.pdf",
    }
    filename = samples.get(sample_key)
    if filename is None:
        raise NotFoundError("Unknown sample document.")
    path = settings.resolved_samples_dir / filename
    if not path.exists():
        raise NotFoundError("Sample PDF is not available. Run samples/generate_samples.py.")
    return filename, path.read_bytes()
