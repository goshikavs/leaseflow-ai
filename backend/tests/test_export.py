from pathlib import Path

from app.schemas.export import ApprovedLeaseExport
from tests.helpers import process_pdf


def _approve_valid(client, sample_pdf: Path) -> str:
    processed = process_pdf(client, sample_pdf)
    lease = client.get(f"/api/v1/leases/{processed['lease_id']}").json()
    approved = client.post(
        f"/api/v1/leases/{lease['id']}/approve",
        json={"version": lease["version"], "reviewed_by": "demo-reviewer"},
    )
    assert approved.status_code == 200
    return lease["id"]


def test_export_approved_record(client, sample_pdf: Path) -> None:
    lease_id = _approve_valid(client, sample_pdf)
    response = client.get(f"/api/v1/leases/{lease_id}/export")
    assert response.status_code == 200
    payload = response.json()
    ApprovedLeaseExport.model_validate(payload)
    assert payload["schema_version"] == "1.0"
    assert payload["source_system"] == "leaseflow-ai"
    assert payload["tenant"]["name"] == "Northwind Analytics LLC"
    assert payload["financial_terms"]["monthly_base_rent"] == "18500.00"
    assert payload["important_dates"]["commencement"] == "2026-01-01"
    assert payload["review"]["status"] == "approved"


def test_reject_unapproved_export(client, sample_pdf: Path) -> None:
    processed = process_pdf(client, sample_pdf)
    response = client.get(f"/api/v1/leases/{processed['lease_id']}/export")
    assert response.status_code == 409


def test_export_contract_validation() -> None:
    payload = {
        "schema_version": "1.0",
        "source_system": "leaseflow-ai",
        "lease_id": "example-lease-id",
        "tenant": {"name": "Acme Technologies"},
        "property": {"address": "100 Example Plaza, Dallas, TX"},
        "financial_terms": {"monthly_base_rent": "18500.00", "currency": "USD"},
        "important_dates": {
            "commencement": "2026-01-01",
            "expiration": "2028-12-31",
            "renewal_notice_days": 180,
        },
        "review": {"status": "approved", "approved_by": "demo-reviewer"},
    }
    parsed = ApprovedLeaseExport.model_validate(payload)
    assert parsed.financial_terms.monthly_base_rent == "18500.00"
