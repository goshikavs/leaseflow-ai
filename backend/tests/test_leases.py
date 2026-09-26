from pathlib import Path

from tests.helpers import process_pdf


def test_lease_update_and_audit(client, missing_pdf: Path) -> None:
    processed = process_pdf(client, missing_pdf)
    lease_id = processed["lease_id"]
    current = client.get(f"/api/v1/leases/{lease_id}").json()
    response = client.patch(
        f"/api/v1/leases/{lease_id}",
        json={
            "version": current["version"],
            "tenant_name": "Cedar and Pine Consulting Inc.",
            "landlord_name": "Westbridge Capital LLC",
            "property_address": "410 Example Parkway, Denver, CO 80202",
            "commencement_date": "2026-03-15",
            "expiration_date": "2027-03-14",
            "monthly_base_rent": "9600.00",
            "currency": "USD",
            "renewal_notice_days": 90,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["property_address"] == "410 Example Parkway, Denver, CO 80202"
    assert body["version"] == current["version"] + 1
    open_blocking = [
        issue for issue in body["issues"] if issue["resolved_at"] is None and issue["severity"] == "blocking"
    ]
    assert open_blocking == []

    audit = client.get(f"/api/v1/leases/{lease_id}/audit").json()
    types = {item["event_type"] for item in audit}
    assert "lease_corrected" in types
    assert "processing_completed" in types


def test_optimistic_concurrency(client, sample_pdf: Path) -> None:
    processed = process_pdf(client, sample_pdf)
    lease_id = processed["lease_id"]
    current = client.get(f"/api/v1/leases/{lease_id}").json()
    stale = client.patch(
        f"/api/v1/leases/{lease_id}",
        json={"version": current["version"] - 1 if current["version"] > 0 else 0, "tenant_name": "Wrong"},
    )
    # version 1 is current after processing; send an older version
    stale = client.patch(
        f"/api/v1/leases/{lease_id}",
        json={"version": 0, "tenant_name": "Wrong"},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "VERSION_CONFLICT"


def test_approve_valid_lease(client, sample_pdf: Path) -> None:
    processed = process_pdf(client, sample_pdf)
    lease_id = processed["lease_id"]
    current = client.get(f"/api/v1/leases/{lease_id}").json()
    response = client.post(
        f"/api/v1/leases/{lease_id}/approve",
        json={"version": current["version"], "reviewed_by": "demo-reviewer"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["approved_by"] == "demo-reviewer"


def test_reject_invalid_approval(client, missing_pdf: Path) -> None:
    processed = process_pdf(client, missing_pdf)
    lease_id = processed["lease_id"]
    current = client.get(f"/api/v1/leases/{lease_id}").json()
    response = client.post(
        f"/api/v1/leases/{lease_id}/approve",
        json={"version": current["version"], "reviewed_by": "demo-reviewer"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "BLOCKING_ISSUES"


def test_conflicting_dates_block_approval(client, conflicting_pdf: Path) -> None:
    processed = process_pdf(client, conflicting_pdf)
    lease = client.get(f"/api/v1/leases/{processed['lease_id']}").json()
    codes = {issue["issue_code"] for issue in lease["issues"] if issue["resolved_at"] is None}
    assert "INVALID_DATE_RANGE" in codes
    response = client.post(
        f"/api/v1/leases/{lease['id']}/approve",
        json={"version": lease["version"], "reviewed_by": "demo-reviewer"},
    )
    assert response.status_code == 422
