from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TenantContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None


class PropertyContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    address: str | None


class FinancialTermsContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    monthly_base_rent: str | None
    currency: str | None


class ImportantDatesContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    commencement: str | None
    expiration: str | None
    renewal_notice_days: int | None


class ReviewContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    approved_by: str | None


class ApprovedLeaseExport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(pattern=r"^\d+\.\d+$")
    source_system: str
    lease_id: str
    tenant: TenantContract
    property: PropertyContract
    financial_terms: FinancialTermsContract
    important_dates: ImportantDatesContract
    review: ReviewContract

    def payload_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
