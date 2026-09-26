from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ConfidenceLiteral = Literal["evidence_found", "missing", "unsupported_evidence"]
FIELD_NAMES = (
    "tenant_name",
    "landlord_name",
    "property_address",
    "commencement_date",
    "expiration_date",
    "monthly_base_rent",
    "currency",
    "renewal_notice_days",
)


class ExtractedField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    source_text: str | None = None
    confidence_status: ConfidenceLiteral


class LeaseExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_name: ExtractedField
    landlord_name: ExtractedField
    property_address: ExtractedField
    commencement_date: ExtractedField
    expiration_date: ExtractedField
    monthly_base_rent: ExtractedField
    currency: ExtractedField
    renewal_notice_days: ExtractedField

    def field_map(self) -> dict[str, ExtractedField]:
        return {name: getattr(self, name) for name in FIELD_NAMES}


class ParsedPage(BaseModel):
    page_number: int
    text: str


class ParsedDocument(BaseModel):
    page_count: int
    pages: list[ParsedPage]

    @property
    def full_text(self) -> str:
        return "\n".join(page.text for page in self.pages)
