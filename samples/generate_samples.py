"""Generate fictional commercial lease PDFs and a fixture manifest."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_pdf(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=letter, invariant=1)
    pdf.setTitle(title)
    pdf.setFont("Times-Roman", 16)
    pdf.drawString(72, 720, title)
    pdf.setFont("Times-Roman", 11)
    y = 680
    for line in lines:
        pdf.drawString(72, y, line)
        y -= 18
        if y < 72:
            pdf.showPage()
            pdf.setFont("Times-Roman", 11)
            y = 720
    pdf.save()


def field(value: str | None, page: int | None, source: str | None, status: str) -> dict:
    return {
        "value": value,
        "page_number": page,
        "source_text": source,
        "confidence_status": status,
    }


def missing() -> dict:
    return field(None, None, None, "missing")


def build_samples() -> dict:
    valid_lines = [
        "This Office Lease Agreement is made for demonstration purposes only.",
        "This document is fictional and does not provide legal advice.",
        "Tenant: Northwind Analytics LLC",
        "Landlord: Harborpoint Realty Partners LLC",
        "Property Address: 1200 Commerce Street, Suite 400, Dallas, TX 75201",
        "Commencement Date: 2026-01-01",
        "Expiration Date: 2028-12-31",
        "Monthly Base Rent: 18500.00 USD",
        "Renewal Notice: Tenant shall give 180 days prior written notice to renew.",
        "The parties agree this synthetic lease is intended only for software testing.",
    ]
    missing_lines = [
        "This Office Lease Agreement is incomplete by design.",
        "This document is fictional and does not provide legal advice.",
        "Tenant: Cedar and Pine Consulting Inc.",
        "Landlord information is not stated in this draft.",
        "The premises description was omitted from this draft.",
        "Commencement Date: 2026-03-15",
        "Expiration Date: 2027-03-14",
        "Monthly Base Rent is not specified in this draft.",
        "Renewal Notice: Tenant shall give 90 days prior written notice to renew.",
    ]
    conflict_lines = [
        "This Office Lease Agreement contains conflicting dates by design.",
        "This document is fictional and does not provide legal advice.",
        "Tenant: Brightline Logistics LLC",
        "Landlord: Summitcrest Holdings LLC",
        "Property Address: 88 Market Avenue, Floor 12, Austin, TX 78701",
        "Commencement Date: 2027-06-01",
        "Expiration Date: 2026-05-31",
        "Monthly Base Rent: 14250.00 USD",
        "Renewal Notice: Tenant shall give 120 days prior written notice to renew.",
        "The stated expiration precedes the stated commencement and requires review.",
    ]

    valid_path = ROOT / "sample_lease.pdf"
    missing_path = ROOT / "missing_fields_lease.pdf"
    conflict_path = ROOT / "conflicting_dates_lease.pdf"
    prosper_path = ROOT / "prosper_retail_lease.pdf"
    dallas_path = ROOT / "dallas_plaza_lease.pdf"
    logistics_path = ROOT / "logistics_park_lease.pdf"
    large_path = ROOT / "logistics_park_large.pdf"
    amendment_path = ROOT / "logistics_park_amendment.pdf"

    _write_pdf(valid_path, "Office Lease Agreement - Northwind Analytics LLC", valid_lines)
    _write_pdf(missing_path, "Office Lease Agreement - Cedar and Pine Consulting Inc.", missing_lines)
    _write_pdf(conflict_path, "Office Lease Agreement - Brightline Logistics LLC", conflict_lines)
    _write_pdf(prosper_path, "Retail Lease Agreement - Northstar Coffee LLC", _prosper_lines())
    _write_pdf(dallas_path, "Office Lease Agreement - Atlas Technology Services LLC", _dallas_lines())
    _write_pdf(logistics_path, "Industrial Lease Agreement - Meridian Distribution LLC", _logistics_lines())
    _write_pdf(large_path, "Industrial Lease Exhibits - Meridian Distribution LLC", _large_logistics_lines())
    _write_pdf(amendment_path, "First Amendment - Meridian Distribution LLC", _amendment_lines())

    samples = [
        {
            "key": "sample_lease",
            "filename": "sample_lease.pdf",
            "description": "Complete valid fictional lease",
            "content_hash": _sha256(valid_path),
            "extraction": {
                "tenant_name": field("Northwind Analytics LLC", 1, "Tenant: Northwind Analytics LLC", "evidence_found"),
                "landlord_name": field(
                    "Harborpoint Realty Partners LLC",
                    1,
                    "Landlord: Harborpoint Realty Partners LLC",
                    "evidence_found",
                ),
                "property_address": field(
                    "1200 Commerce Street, Suite 400, Dallas, TX 75201",
                    1,
                    "Property Address: 1200 Commerce Street, Suite 400, Dallas, TX 75201",
                    "evidence_found",
                ),
                "commencement_date": field("2026-01-01", 1, "Commencement Date: 2026-01-01", "evidence_found"),
                "expiration_date": field("2028-12-31", 1, "Expiration Date: 2028-12-31", "evidence_found"),
                "monthly_base_rent": field("18500.00", 1, "Monthly Base Rent: 18500.00 USD", "evidence_found"),
                "currency": field("USD", 1, "Monthly Base Rent: 18500.00 USD", "evidence_found"),
                "renewal_notice_days": field(
                    "180",
                    1,
                    "Renewal Notice: Tenant shall give 180 days prior written notice to renew.",
                    "evidence_found",
                ),
            },
        },
        {
            "key": "missing_fields_lease",
            "filename": "missing_fields_lease.pdf",
            "description": "Lease missing landlord, property, and rent",
            "content_hash": _sha256(missing_path),
            "extraction": {
                "tenant_name": field(
                    "Cedar and Pine Consulting Inc.",
                    1,
                    "Tenant: Cedar and Pine Consulting Inc.",
                    "evidence_found",
                ),
                "landlord_name": missing(),
                "property_address": missing(),
                "commencement_date": field("2026-03-15", 1, "Commencement Date: 2026-03-15", "evidence_found"),
                "expiration_date": field("2027-03-14", 1, "Expiration Date: 2027-03-14", "evidence_found"),
                "monthly_base_rent": missing(),
                "currency": missing(),
                "renewal_notice_days": field(
                    "90",
                    1,
                    "Renewal Notice: Tenant shall give 90 days prior written notice to renew.",
                    "evidence_found",
                ),
            },
        },
        {
            "key": "conflicting_dates_lease",
            "filename": "conflicting_dates_lease.pdf",
            "description": "Lease whose expiration precedes commencement",
            "content_hash": _sha256(conflict_path),
            "extraction": {
                "tenant_name": field("Brightline Logistics LLC", 1, "Tenant: Brightline Logistics LLC", "evidence_found"),
                "landlord_name": field(
                    "Summitcrest Holdings LLC",
                    1,
                    "Landlord: Summitcrest Holdings LLC",
                    "evidence_found",
                ),
                "property_address": field(
                    "88 Market Avenue, Floor 12, Austin, TX 78701",
                    1,
                    "Property Address: 88 Market Avenue, Floor 12, Austin, TX 78701",
                    "evidence_found",
                ),
                "commencement_date": field("2027-06-01", 1, "Commencement Date: 2027-06-01", "evidence_found"),
                "expiration_date": field("2026-05-31", 1, "Expiration Date: 2026-05-31", "evidence_found"),
                "monthly_base_rent": field("14250.00", 1, "Monthly Base Rent: 14250.00 USD", "evidence_found"),
                "currency": field("USD", 1, "Monthly Base Rent: 14250.00 USD", "evidence_found"),
                "renewal_notice_days": field(
                    "120",
                    1,
                    "Renewal Notice: Tenant shall give 120 days prior written notice to renew.",
                    "evidence_found",
                ),
            },
        },
        _sample(
            "prosper_retail_lease",
            "prosper_retail_lease.pdf",
            "Property A retail lease for Prosper Retail Center",
            prosper_path,
            tenant="Northstar Coffee LLC",
            landlord="Harborpoint Realty Partners LLC",
            address="100 Prosper Crossing, Prosper, TX 75078",
            start="2026-01-01",
            end="2028-12-31",
            rent="4200.00",
            notice="90",
        ),
        _sample(
            "dallas_plaza_lease",
            "dallas_plaza_lease.pdf",
            "Property B office lease for Dallas Corporate Plaza",
            dallas_path,
            tenant="Atlas Technology Services LLC",
            landlord="Harborpoint Realty Partners LLC",
            address="2200 Ross Avenue, Suite 1800, Dallas, TX 75201",
            start="2026-04-01",
            end="2031-03-31",
            rent="78000.00",
            notice="180",
        ),
        _sample(
            "logistics_park_lease",
            "logistics_park_lease.pdf",
            "Property C industrial lease for North Texas Logistics Park",
            logistics_path,
            tenant="Meridian Distribution LLC",
            landlord="Harborpoint Realty Partners LLC",
            address="4800 Belt Line Road, Building 7, Irving, TX 75038",
            start="2026-02-01",
            end="2031-01-31",
            rent="31500.00",
            notice="120",
        ),
        _sample(
            "logistics_park_large",
            "logistics_park_large.pdf",
            "Large multipage industrial exhibit set",
            large_path,
            tenant="Meridian Distribution LLC",
            landlord="Harborpoint Realty Partners LLC",
            address="4800 Belt Line Road, Building 7, Irving, TX 75038",
            start="2026-02-01",
            end="2031-01-31",
            rent="31500.00",
            notice="120",
        ),
        {
            "key": "logistics_park_amendment",
            "filename": "logistics_park_amendment.pdf",
            "description": "Amendment that supersedes Property C rent",
            "content_hash": _sha256(amendment_path),
            "extraction": {
                "tenant_name": field(
                    "Meridian Distribution LLC", 1, "Tenant: Meridian Distribution LLC", "evidence_found"
                ),
                "landlord_name": field(
                    "Harborpoint Realty Partners LLC",
                    1,
                    "Landlord: Harborpoint Realty Partners LLC",
                    "evidence_found",
                ),
                "property_address": field(
                    "4800 Belt Line Road, Building 7, Irving, TX 75038",
                    1,
                    "Property Address: 4800 Belt Line Road, Building 7, Irving, TX 75038",
                    "evidence_found",
                ),
                "commencement_date": field("2026-07-01", 1, "Commencement Date: 2026-07-01", "evidence_found"),
                "expiration_date": field("2031-01-31", 1, "Expiration Date: 2031-01-31", "evidence_found"),
                "monthly_base_rent": field("34800.00", 1, "Monthly Base Rent is hereby increased to 34800.00 USD", "evidence_found"),
                "currency": field("USD", 1, "Monthly Base Rent is hereby increased to 34800.00 USD", "evidence_found"),
                "renewal_notice_days": field(
                    "120",
                    1,
                    "Renewal Notice: Tenant shall give 120 days prior written notice to renew.",
                    "evidence_found",
                ),
            },
        },
    ]
    return {"schema_version": "1.0", "samples": samples}


def _sample(
    key: str,
    filename: str,
    description: str,
    path: Path,
    *,
    tenant: str,
    landlord: str,
    address: str,
    start: str,
    end: str,
    rent: str,
    notice: str,
) -> dict:
    return {
        "key": key,
        "filename": filename,
        "description": description,
        "content_hash": _sha256(path),
        "extraction": {
            "tenant_name": field(tenant, 1, f"Tenant: {tenant}", "evidence_found"),
            "landlord_name": field(landlord, 1, f"Landlord: {landlord}", "evidence_found"),
            "property_address": field(address, 1, f"Property Address: {address}", "evidence_found"),
            "commencement_date": field(start, 1, f"Commencement Date: {start}", "evidence_found"),
            "expiration_date": field(end, 1, f"Expiration Date: {end}", "evidence_found"),
            "monthly_base_rent": field(rent, 1, f"Monthly Base Rent: {rent} USD", "evidence_found"),
            "currency": field("USD", 1, f"Monthly Base Rent: {rent} USD", "evidence_found"),
            "renewal_notice_days": field(
                notice,
                1,
                f"Renewal Notice: Tenant shall give {notice} days prior written notice to renew.",
                "evidence_found",
            ),
        },
    }


def _common_clauses(property_name: str, property_type: str) -> list[str]:
    return [
        f"This document is fictional and does not provide legal advice. Property: {property_name}.",
        f"Property Type: {property_type}.",
        "RENT SCHEDULE",
        "Base rent is payable monthly in advance on the first business day.",
        "RENEWAL OPTIONS",
        "Tenant may renew for one additional three-year term if not in default.",
        "NOTICE REQUIREMENTS",
        "Notices must be delivered by certified mail or nationally recognized overnight courier.",
        "MAINTENANCE CLAUSES",
        "Landlord maintains structural elements; Tenant maintains interior finish and storefront glass.",
        "INSURANCE REQUIREMENTS",
        "Tenant shall carry commercial general liability insurance of at least two million dollars.",
        "OPERATING EXPENSES",
        "Tenant shall pay its proportionate share of documented common area operating expenses.",
        "SECURITY DEPOSIT",
        "Tenant shall deposit two months of base rent as a security deposit.",
        "ASSIGNMENT AND SUBLEASING",
        "Assignment or sublease requires Landlord's prior written consent, not to be unreasonably withheld.",
        "TERMINATION PROVISIONS",
        "Either party may terminate for material default uncured after thirty days written notice.",
    ]


def _prosper_lines() -> list[str]:
    return [
        "This Retail Lease Agreement is made for demonstration purposes only.",
        "Tenant: Northstar Coffee LLC",
        "Landlord: Harborpoint Realty Partners LLC",
        "Property Address: 100 Prosper Crossing, Prosper, TX 75078",
        "Commencement Date: 2026-01-01",
        "Expiration Date: 2028-12-31",
        "Monthly Base Rent: 4200.00 USD",
        "Renewal Notice: Tenant shall give 90 days prior written notice to renew.",
        *_common_clauses("Prosper Retail Center", "Retail"),
        "Percentage rent does not apply to this coffee-use demise.",
    ]


def _dallas_lines() -> list[str]:
    return [
        "This Office Lease Agreement is made for demonstration purposes only.",
        "Tenant: Atlas Technology Services LLC",
        "Landlord: Harborpoint Realty Partners LLC",
        "Property Address: 2200 Ross Avenue, Suite 1800, Dallas, TX 75201",
        "Commencement Date: 2026-04-01",
        "Expiration Date: 2031-03-31",
        "Monthly Base Rent: 78000.00 USD",
        "Renewal Notice: Tenant shall give 180 days prior written notice to renew.",
        *_common_clauses("Dallas Corporate Plaza", "Office"),
        "After-hours HVAC is billed at the posted building rate.",
        "A tenant improvement allowance of sixty dollars per rentable square foot is documented.",
    ]


def _logistics_lines() -> list[str]:
    return [
        "This Industrial Lease Agreement is made for demonstration purposes only.",
        "Tenant: Meridian Distribution LLC",
        "Landlord: Harborpoint Realty Partners LLC",
        "Property Address: 4800 Belt Line Road, Building 7, Irving, TX 75038",
        "Commencement Date: 2026-02-01",
        "Expiration Date: 2031-01-31",
        "Monthly Base Rent: 31500.00 USD",
        "Renewal Notice: Tenant shall give 120 days prior written notice to renew.",
        *_common_clauses("North Texas Logistics Park", "Industrial"),
        "Clear height is thirty-two feet with fifty-two dock positions.",
        "Tenant is responsible for racking, material handling equipment, and trailer storage rules.",
    ]


def _large_logistics_lines() -> list[str]:
    pages: list[str] = _logistics_lines()
    exhibits = [
        "EXHIBIT A LEGAL DESCRIPTION",
        "The land is a 28.4 acre industrial tract in Dallas County described by metes and bounds exhibit.",
        "EXHIBIT B SITE PLAN",
        "Building 7 is the eastern warehouse with exclusive truck court and shared drive aisle access.",
        "EXHIBIT C RENT ESCALATION",
        "Annual escalations of three percent apply on each anniversary of the commencement date.",
        "EXHIBIT D MAINTENANCE MATRIX",
        "Roof, structure, and parking lot structural repairs remain Landlord obligations.",
        "EXHIBIT E ENVIRONMENTAL",
        "Tenant shall not introduce hazardous materials except ordinary warehouse quantities.",
        "EXHIBIT F INSURANCE SCHEDULE",
        "Umbrella coverage of ten million dollars is required in addition to primary liability.",
        "EXHIBIT G ACCESS CONTROL",
        "After-hours gate codes are issued to named managers and must be rotated quarterly.",
        "EXHIBIT H UTILITIES",
        "Electricity, water, and trash are separately metered and paid directly by Tenant.",
        "EXHIBIT I PARKING",
        "Automobile parking is limited to fifty spaces; trailer parking uses the designated stalls.",
        "EXHIBIT J SIGNAGE",
        "Building monument signage is limited to tenant's legal name and standard logo colors.",
        "EXHIBIT K RESTORATION",
        "At surrender Tenant shall remove racking and repair floor penetrations to warehouse standard.",
        "EXHIBIT L FORCE MAJEURE",
        "Delays from named storms, government orders, or utility failure extend performance dates.",
        "EXHIBIT M DISPUTE RESOLUTION",
        "The parties first mediate in Dallas County before any court proceeding.",
        "EXHIBIT N SNDA",
        "Tenant agrees to execute a commercially reasonable subordination and non-disturbance agreement.",
        "EXHIBIT O RULES",
        "Idling time, dock scheduling, and overnight trailer storage follow the park rules packet.",
    ]
    filler = []
    for exhibit in exhibits:
        filler.append(exhibit)
        filler.append(f"Additional narrative for {exhibit}: this clause is unique and intended for retrieval tests.")
        filler.append(f"Operational note associated with {exhibit} describes only fictional warehouse practice.")
    return pages + filler


def _amendment_lines() -> list[str]:
    return [
        "This First Amendment shall supersede the monthly base rent stated in the original lease.",
        "This document is fictional and does not provide legal advice.",
        "Tenant: Meridian Distribution LLC",
        "Landlord: Harborpoint Realty Partners LLC",
        "Property Address: 4800 Belt Line Road, Building 7, Irving, TX 75038",
        "Commencement Date: 2026-07-01",
        "Expiration Date: 2031-01-31",
        "Monthly Base Rent is hereby increased to 34800.00 USD",
        "Renewal Notice: Tenant shall give 120 days prior written notice to renew.",
        "The parties agree the increased rent creates a documented conflict with the original rent schedule.",
        "All other original lease terms remain in effect except as expressly superseded.",
    ]


def main() -> int:
    manifest = build_samples()
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Generated sample PDFs and manifest.json")
    for sample in manifest["samples"]:
        print(f"  {sample['filename']} {sample['content_hash']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
