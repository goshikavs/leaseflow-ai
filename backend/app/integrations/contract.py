from decimal import Decimal

from app.models.lease import Lease
from app.schemas.export import (
    ApprovedLeaseExport,
    FinancialTermsContract,
    ImportantDatesContract,
    PropertyContract,
    ReviewContract,
    TenantContract,
)

SCHEMA_VERSION = "1.0"
SOURCE_SYSTEM = "leaseflow-ai"


def build_export_payload(lease: Lease) -> ApprovedLeaseExport:
    rent = lease.monthly_base_rent
    rent_value = f"{Decimal(rent).quantize(Decimal('0.01')):.2f}" if rent is not None else None
    return ApprovedLeaseExport(
        schema_version=SCHEMA_VERSION,
        source_system=SOURCE_SYSTEM,
        lease_id=lease.id,
        tenant=TenantContract(name=lease.tenant_name),
        property=PropertyContract(address=lease.property_address),
        financial_terms=FinancialTermsContract(
            monthly_base_rent=rent_value,
            currency=lease.currency,
        ),
        important_dates=ImportantDatesContract(
            commencement=lease.commencement_date.isoformat() if lease.commencement_date else None,
            expiration=lease.expiration_date.isoformat() if lease.expiration_date else None,
            renewal_notice_days=lease.renewal_notice_days,
        ),
        review=ReviewContract(status=lease.status, approved_by=lease.approved_by),
    )
