from pathlib import Path

from tests.helpers import process_pdf, upload_pdf


def test_valid_pdf_upload(client, sample_pdf: Path) -> None:
    body = upload_pdf(client, sample_pdf)
    assert body["processing_status"] == "uploaded"
    assert body["original_filename"] == "sample_lease.pdf"
    assert len(body["content_hash"]) == 64


def test_invalid_file_rejection(client) -> None:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_FILE_TYPE"


def test_invalid_pdf_header(client) -> None:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("fake.pdf", b"XXXX-not-a-pdf", "application/pdf")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PDF_CONTENT"


def test_oversized_pdf_rejection(client, sample_pdf: Path, monkeypatch) -> None:
    from app.core.config import get_settings

    monkeypatch.setenv("MAX_UPLOAD_BYTES", "128")
    get_settings.cache_clear()
    response = client.post(
        "/api/v1/documents",
        files={"file": (sample_pdf.name, sample_pdf.read_bytes(), "application/pdf")},
    )
    get_settings.cache_clear()
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "10485760")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_document_get_and_stats(client, sample_pdf: Path) -> None:
    uploaded = upload_pdf(client, sample_pdf)
    detail = client.get(f"/api/v1/documents/{uploaded['id']}")
    assert detail.status_code == 200
    stats = client.get("/api/v1/stats")
    assert stats.status_code == 200
    assert stats.json()["total_documents"] == 1


def test_duplicate_processing_does_not_create_second_lease(client, sample_pdf: Path) -> None:
    first = process_pdf(client, sample_pdf)
    second = client.post(f"/api/v1/documents/{first['document']['id']}/process")
    assert second.status_code == 200
    assert second.json()["lease_id"] == first["lease_id"]
    leases = client.get("/api/v1/leases")
    assert leases.json()["total"] == 1
