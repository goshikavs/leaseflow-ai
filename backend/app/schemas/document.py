from datetime import datetime

from pydantic import BaseModel, Field


class DocumentSummary(BaseModel):
    id: str
    original_filename: str
    content_hash: str
    uploaded_at: datetime
    processing_status: str
    processing_error: str | None = None
    lease_id: str | None = None
    organization_id: str | None = None
    property_id: str | None = None
    document_type: str | None = None


class DocumentProcessResponse(BaseModel):
    document: DocumentSummary
    lease_id: str | None = None
    extraction_id: str | None = None
    validation_issue_count: int = 0
    blocking_issue_count: int = 0
    provider: str
    fixture_mode: bool


class StatsResponse(BaseModel):
    total_documents: int
    awaiting_review: int
    approved_leases: int
    processing_errors: int


class SampleInfo(BaseModel):
    key: str
    filename: str
    description: str


class SampleListResponse(BaseModel):
    items: list[SampleInfo] = Field(default_factory=list)
