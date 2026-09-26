from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import db_session, settings_dep
from app.core.config import Settings
from app.models.enums import ProcessingStatus
from app.schemas.common import Page
from app.schemas.document import (
    DocumentProcessResponse,
    DocumentSummary,
    SampleInfo,
    SampleListResponse,
    StatsResponse,
)
from app.services.documents import (
    create_document,
    dashboard_stats,
    document_summary,
    get_document,
    list_documents,
    load_sample_bytes,
)
from app.workflows.processing import process_document

router = APIRouter(prefix="/api/v1", tags=["documents"])


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(db_session)) -> StatsResponse:
    return dashboard_stats(db)


@router.get("/documents", response_model=Page[DocumentSummary])
def get_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(db_session),
) -> Page[DocumentSummary]:
    items, total = list_documents(db, page, page_size)
    return Page(
        items=[document_summary(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("/documents", response_model=DocumentSummary, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    organization_id: str | None = Form(default=None),
    property_id: str | None = Form(default=None),
    document_type: str = Form(default="lease"),
    document_version: int = Form(default=1),
    sample_key: str | None = Form(default=None),
    lease_type: str | None = Form(default=None),
    db: Session = Depends(db_session),
    settings: Settings = Depends(settings_dep),
) -> DocumentSummary:
    data = await file.read()
    document = create_document(
        db,
        settings,
        file.filename or "document.pdf",
        data,
        organization_id=organization_id,
        property_id=property_id,
        document_type=document_type,
        document_version=document_version,
        sample_key=sample_key,
        lease_type=lease_type,
    )
    return document_summary(document)


@router.post("/documents/{document_id}/process", response_model=DocumentProcessResponse)
def process_uploaded_document(
    document_id: str,
    db: Session = Depends(db_session),
    settings: Settings = Depends(settings_dep),
) -> DocumentProcessResponse:
    document = get_document(db, document_id)
    lease = process_document(db, settings, document, settings.demo_actor)
    document = get_document(db, document_id)
    open_issues = [issue for issue in lease.issues if issue.resolved_at is None]
    return DocumentProcessResponse(
        document=document_summary(document),
        lease_id=lease.id,
        extraction_id=lease.document.extractions[-1].id if lease.document.extractions else None,
        validation_issue_count=len(open_issues),
        blocking_issue_count=sum(1 for issue in open_issues if issue.severity == "blocking"),
        provider=settings.extraction_provider,
        fixture_mode=settings.extraction_provider == "fixture",
    )


@router.get("/documents/{document_id}", response_model=DocumentSummary)
def get_uploaded_document(
    document_id: str,
    db: Session = Depends(db_session),
) -> DocumentSummary:
    return document_summary(get_document(db, document_id))


@router.get("/demo/samples", response_model=SampleListResponse)
def list_samples() -> SampleListResponse:
    return SampleListResponse(
        items=[
            SampleInfo(key="sample_lease", filename="sample_lease.pdf", description="Complete valid fictional lease"),
            SampleInfo(
                key="missing_fields_lease",
                filename="missing_fields_lease.pdf",
                description="Lease missing critical fields",
            ),
            SampleInfo(
                key="conflicting_dates_lease",
                filename="conflicting_dates_lease.pdf",
                description="Lease with conflicting dates",
            ),
            SampleInfo(
                key="prosper_retail_lease",
                filename="prosper_retail_lease.pdf",
                description="Property A retail lease",
            ),
            SampleInfo(
                key="dallas_plaza_lease",
                filename="dallas_plaza_lease.pdf",
                description="Property B office lease",
            ),
            SampleInfo(
                key="logistics_park_lease",
                filename="logistics_park_lease.pdf",
                description="Property C industrial lease",
            ),
            SampleInfo(
                key="logistics_park_large",
                filename="logistics_park_large.pdf",
                description="Large industrial exhibit",
            ),
            SampleInfo(
                key="logistics_park_amendment",
                filename="logistics_park_amendment.pdf",
                description="Property C rent amendment",
            ),
        ]
    )


@router.post("/demo/samples/{sample_key}/upload", response_model=DocumentSummary, status_code=201)
def upload_sample(
    sample_key: str,
    organization_id: str | None = None,
    property_id: str | None = None,
    document_type: str = "lease",
    document_version: int = 1,
    lease_type: str | None = None,
    db: Session = Depends(db_session),
    settings: Settings = Depends(settings_dep),
) -> DocumentSummary:
    filename, data = load_sample_bytes(settings, sample_key)
    mapped = {
        "prosper_retail_lease": ("prop-prosper-retail", "lease", 1),
        "dallas_plaza_lease": ("prop-dallas-plaza", "lease", 1),
        "logistics_park_lease": ("prop-ntx-logistics", "lease", 1),
        "logistics_park_large": ("prop-ntx-logistics", "lease", 1),
        "logistics_park_amendment": ("prop-ntx-logistics", "amendment", 2),
    }
    default_property, default_type, default_version = mapped.get(
        sample_key, (property_id, document_type, document_version)
    )
    document = create_document(
        db,
        settings,
        filename,
        data,
        organization_id=organization_id or settings.default_organization_id,
        property_id=property_id or default_property,
        document_type=document_type if sample_key not in mapped else default_type,
        document_version=document_version if sample_key not in mapped else default_version,
        sample_key=sample_key,
        lease_type=lease_type,
    )
    document.processing_status = ProcessingStatus.UPLOADED.value
    db.commit()
    db.refresh(document)
    return document_summary(document)
