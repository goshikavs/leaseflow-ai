from datetime import date
from decimal import Decimal

from app.models.lease import Lease
from app.services.time import utcnow
from app.services.validation import validate_lease_record


def _lease(**overrides: object) -> Lease:
    now = utcnow()
    values = {
        "id": "lease-1",
        "document_id": "doc-1",
        "tenant_name": "Northwind Analytics LLC",
        "landlord_name": "Harborpoint Realty Partners LLC",
        "property_address": "1200 Commerce Street, Suite 400, Dallas, TX 75201",
        "commencement_date": date(2026, 1, 1),
        "expiration_date": date(2028, 12, 31),
        "monthly_base_rent": Decimal("18500.00"),
        "currency": "USD",
        "renewal_notice_days": 180,
        "status": "awaiting_review",
        "created_at": now,
        "updated_at": now,
        "version": 1,
    }
    values.update(overrides)
    return Lease(**values)


def test_valid_lease_dates() -> None:
    issues = validate_lease_record(_lease())
    assert issues == []


def test_invalid_date_range() -> None:
    codes = {issue.issue_code for issue in validate_lease_record(_lease(expiration_date=date(2025, 1, 1)))}
    assert "INVALID_DATE_RANGE" in codes


def test_invalid_rent() -> None:
    codes = {issue.issue_code for issue in validate_lease_record(_lease(monthly_base_rent=Decimal("0")))}
    assert "INVALID_RENT" in codes


def test_renewal_notice_validation() -> None:
    negative = {issue.issue_code for issue in validate_lease_record(_lease(renewal_notice_days=-1))}
    too_long = {
        issue.issue_code
        for issue in validate_lease_record(
            _lease(
                commencement_date=date(2026, 1, 1),
                expiration_date=date(2026, 1, 10),
                renewal_notice_days=30,
            )
        )
    }
    assert "NEGATIVE_NOTICE" in negative
    assert "NOTICE_EXCEEDS_TERM" in too_long
