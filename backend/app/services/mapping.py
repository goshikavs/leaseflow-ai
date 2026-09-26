from datetime import date
from decimal import Decimal, InvalidOperation

from app.extraction.schemas import ExtractedField, LeaseExtractionResult
from app.models.enums import ConfidenceStatus


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def parse_money(value: str | None) -> Decimal | None:
    if not value:
        return None
    cleaned = value.replace("$", "").replace(",", "").strip()
    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        return None
    return amount.quantize(Decimal("0.01"))


def parse_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def authoritative_value(field: ExtractedField) -> str | None:
    if field.confidence_status != ConfidenceStatus.EVIDENCE_FOUND.value:
        return None
    return field.value


def lease_values_from_extraction(result: LeaseExtractionResult) -> dict:
    tenant = authoritative_value(result.tenant_name)
    landlord = authoritative_value(result.landlord_name)
    address = authoritative_value(result.property_address)
    commencement = parse_date(authoritative_value(result.commencement_date))
    expiration = parse_date(authoritative_value(result.expiration_date))
    rent = parse_money(authoritative_value(result.monthly_base_rent))
    currency = authoritative_value(result.currency)
    notice = parse_int(authoritative_value(result.renewal_notice_days))
    return {
        "tenant_name": tenant,
        "landlord_name": landlord,
        "property_address": address,
        "commencement_date": commencement,
        "expiration_date": expiration,
        "monthly_base_rent": rent,
        "currency": currency.upper() if currency else None,
        "renewal_notice_days": notice,
    }
