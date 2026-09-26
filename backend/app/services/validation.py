from datetime import date
from decimal import Decimal

from app.models.enums import IssueSeverity
from app.models.lease import Lease


class IssueDraft:
    def __init__(self, field_name: str, issue_code: str, severity: IssueSeverity, description: str) -> None:
        self.field_name = field_name
        self.issue_code = issue_code
        self.severity = severity
        self.description = description


def _is_blank(value: str | None) -> bool:
    return value is None or not value.strip()


def validate_lease_record(lease: Lease) -> list[IssueDraft]:
    issues: list[IssueDraft] = []

    if _is_blank(lease.tenant_name):
        issues.append(
            IssueDraft(
                "tenant_name",
                "MISSING_TENANT",
                IssueSeverity.BLOCKING,
                "Tenant name is required before approval.",
            )
        )
    if _is_blank(lease.property_address):
        issues.append(
            IssueDraft(
                "property_address",
                "MISSING_PROPERTY",
                IssueSeverity.BLOCKING,
                "Property address is required before approval.",
            )
        )
    if _is_blank(lease.landlord_name):
        issues.append(
            IssueDraft(
                "landlord_name",
                "MISSING_LANDLORD",
                IssueSeverity.WARNING,
                "Landlord name is missing. Confirm the counterparty before downstream use.",
            )
        )
    if lease.commencement_date is None:
        issues.append(
            IssueDraft(
                "commencement_date",
                "MISSING_COMMENCEMENT",
                IssueSeverity.BLOCKING,
                "Commencement date is required and must be an explicit calendar date.",
            )
        )
    if lease.expiration_date is None:
        issues.append(
            IssueDraft(
                "expiration_date",
                "MISSING_EXPIRATION",
                IssueSeverity.BLOCKING,
                "Expiration date is required and must be an explicit calendar date.",
            )
        )
    if (
        isinstance(lease.commencement_date, date)
        and isinstance(lease.expiration_date, date)
        and lease.commencement_date >= lease.expiration_date
    ):
        issues.append(
            IssueDraft(
                "expiration_date",
                "INVALID_DATE_RANGE",
                IssueSeverity.BLOCKING,
                "Commencement date must precede expiration date.",
            )
        )
    if lease.monthly_base_rent is None:
        issues.append(
            IssueDraft(
                "monthly_base_rent",
                "MISSING_RENT",
                IssueSeverity.BLOCKING,
                "Monthly base rent is required before approval.",
            )
        )
    elif lease.monthly_base_rent <= Decimal("0"):
        issues.append(
            IssueDraft(
                "monthly_base_rent",
                "INVALID_RENT",
                IssueSeverity.BLOCKING,
                "Monthly base rent must be greater than zero.",
            )
        )
    if lease.currency and len(lease.currency) != 3:
        issues.append(
            IssueDraft(
                "currency",
                "UNEXPECTED_CURRENCY",
                IssueSeverity.WARNING,
                "Currency should be a three-letter ISO code.",
            )
        )
    if lease.renewal_notice_days is None:
        issues.append(
            IssueDraft(
                "renewal_notice_days",
                "MISSING_RENEWAL_NOTICE",
                IssueSeverity.WARNING,
                "Renewal notice period was not provided.",
            )
        )
    elif lease.renewal_notice_days < 0:
        issues.append(
            IssueDraft(
                "renewal_notice_days",
                "NEGATIVE_NOTICE",
                IssueSeverity.BLOCKING,
                "Renewal notice days cannot be negative.",
            )
        )
    elif (
        lease.commencement_date
        and lease.expiration_date
        and lease.commencement_date < lease.expiration_date
        and lease.renewal_notice_days > (lease.expiration_date - lease.commencement_date).days
    ):
        issues.append(
            IssueDraft(
                "renewal_notice_days",
                "NOTICE_EXCEEDS_TERM",
                IssueSeverity.BLOCKING,
                "Renewal notice period cannot exceed the lease term.",
            )
        )

    return issues
