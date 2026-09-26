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
    pdf = canvas.Canvas(str(path), pagesize=letter)
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

    _write_pdf(valid_path, "Office Lease Agreement - Northwind Analytics LLC", valid_lines)
    _write_pdf(missing_path, "Office Lease Agreement - Cedar and Pine Consulting Inc.", missing_lines)
    _write_pdf(conflict_path, "Office Lease Agreement - Brightline Logistics LLC", conflict_lines)

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
    ]
    return {"schema_version": "1.0", "samples": samples}


def main() -> int:
    manifest = build_samples()
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Generated sample PDFs and manifest.json")
    for sample in manifest["samples"]:
        print(f"  {sample['filename']} {sample['content_hash']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
