from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FieldEvidenceOut(BaseModel):
    field_name: str
    page_number: int | None
    source_text: str | None
    extracted_value: str | None
    confidence_status: str


class ValidationIssueOut(BaseModel):
    id: str
    field_name: str
    issue_code: str
    severity: str
    description: str
    resolved_at: datetime | None


class AuditEventOut(BaseModel):
    id: str
    event_type: str
    actor: str
    change_details: dict[str, Any]
    occurred_at: datetime


class LeaseSummary(BaseModel):
    id: str
    document_id: str
    original_filename: str | None = None
    tenant_name: str | None
    landlord_name: str | None
    property_address: str | None
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
    blocking_issue_count: int = 0


class LeaseDetail(BaseModel):
    id: str
    document_id: str
    original_filename: str | None = None
    processing_status: str | None = None
    tenant_name: str | None
    landlord_name: str | None
    property_address: str | None
    commencement_date: date | None
    expiration_date: date | None
    monthly_base_rent: Decimal | None
    currency: str | None
    renewal_notice_days: int | None
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
    approved_by: str | None = None
    approved_at: datetime | None = None
    extraction_provider: str | None = None
    fixture_mode: bool = False
    organization_id: str | None = None
    property_id: str | None = None
    approval_source: str | None = None
    evidence: list[FieldEvidenceOut] = Field(default_factory=list)
    issues: list[ValidationIssueOut] = Field(default_factory=list)


class LeaseUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    version: int
    tenant_name: str | None = None
    landlord_name: str | None = None
    property_address: str | None = None
    commencement_date: date | None = None
    expiration_date: date | None = None
    monthly_base_rent: Decimal | None = None
    currency: str | None = None
    renewal_notice_days: int | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        return value.upper()

    @field_validator("monthly_base_rent")
    @classmethod
    def normalize_rent(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return value.quantize(Decimal("0.01"))


class ApproveRequest(BaseModel):
    reviewed_by: str | None = Field(default=None, max_length=128)
    version: int
