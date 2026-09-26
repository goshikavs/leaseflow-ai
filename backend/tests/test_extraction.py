import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.errors import AppError, ValidationAppError
from app.extraction.evidence import passage_exists, verify_field
from app.extraction.pdf import parse_pdf
from app.extraction.providers.fixture import FixtureExtractionProvider
from app.extraction.schemas import ExtractedField, ParsedDocument, ParsedPage
from tests.helpers import process_pdf


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_document_text_extraction(sample_pdf: Path) -> None:
    parsed = parse_pdf(sample_pdf)
    assert parsed.page_count >= 1
    assert "Northwind Analytics LLC" in parsed.full_text
    assert "1200 Commerce Street" in parsed.full_text


def test_fixture_extraction_matches_document_text(sample_pdf: Path) -> None:
    parsed = parse_pdf(sample_pdf)
    provider = FixtureExtractionProvider(sample_pdf.parent)
    result = provider.extract(parsed, _sha256(sample_pdf), "unused.pdf")
    assert result.tenant_name.value == "Northwind Analytics LLC"
    assert result.tenant_name.source_text in parsed.full_text


def test_fixture_does_not_match_filename_alone(sample_pdf: Path) -> None:
    parsed = parse_pdf(sample_pdf)
    provider = FixtureExtractionProvider(sample_pdf.parent)
    result = provider.extract(parsed, "0" * 64, "sample_lease.pdf")
    assert result.tenant_name.value is None
    assert result.tenant_name.confidence_status == "missing"


def test_explicit_sample_key_selects_fixture(sample_pdf: Path) -> None:
    parsed = parse_pdf(sample_pdf)
    provider = FixtureExtractionProvider(sample_pdf.parent)
    result = provider.extract(parsed, "0" * 64, "renamed.pdf", sample_key="sample_lease")
    assert result.tenant_name.value == "Northwind Analytics LLC"


def test_fixture_sample_key_mismatch_raises(sample_pdf: Path) -> None:
    parsed = parse_pdf(sample_pdf)
    provider = FixtureExtractionProvider(sample_pdf.parent)
    with pytest.raises(ValidationAppError) as exc:
        provider.extract(
            parsed,
            _sha256(sample_pdf),
            "sample_lease.pdf",
            sample_key="prosper_retail_lease",
        )
    assert exc.value.code == "FIXTURE_ID_MISMATCH"


def test_unknown_document_does_not_receive_fixture_data() -> None:
    document = ParsedDocument(page_count=1, pages=[ParsedPage(page_number=1, text="Unrelated office memo")])
    provider = FixtureExtractionProvider(Path(__file__).resolve().parents[2] / "samples")
    result = provider.extract(document, "0" * 64, "unknown.pdf")
    assert result.tenant_name.value is None
    assert result.tenant_name.confidence_status == "missing"


def test_unsupported_evidence_is_flagged() -> None:
    document = ParsedDocument(page_count=1, pages=[ParsedPage(page_number=1, text="Tenant: Example")])
    field = ExtractedField(
        value="Invented Tenant",
        page_number=1,
        source_text="this passage is not in the document",
        confidence_status="evidence_found",
    )
    verified = verify_field(field, document)
    assert verified.confidence_status == "unsupported_evidence"
    assert not passage_exists("this passage is not in the document", document, 1)


def test_missing_fields_are_persisted(client, missing_pdf: Path) -> None:
    processed = process_pdf(client, missing_pdf)
    lease = client.get(f"/api/v1/leases/{processed['lease_id']}").json()
    assert lease["property_address"] is None
    assert lease["monthly_base_rent"] is None
    codes = {issue["issue_code"] for issue in lease["issues"] if issue["resolved_at"] is None}
    assert "MISSING_PROPERTY" in codes
    assert "MISSING_RENT" in codes


def test_correct_extraction_persistence(client, sample_pdf: Path) -> None:
    processed = process_pdf(client, sample_pdf)
    lease = client.get(f"/api/v1/leases/{processed['lease_id']}").json()
    assert lease["tenant_name"] == "Northwind Analytics LLC"
    assert lease["monthly_base_rent"] == "18500.00"
    evidence = {item["field_name"]: item for item in lease["evidence"]}
    assert evidence["tenant_name"]["confidence_status"] == "evidence_found"
    assert "Northwind Analytics LLC" in evidence["tenant_name"]["source_text"]


def test_malformed_llm_response(client, sample_pdf: Path, monkeypatch) -> None:
    from app.core.config import get_settings
    from app.extraction.providers.llm import OpenAICompatibleProvider

    monkeypatch.setenv("EXTRACTION_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    get_settings.cache_clear()

    def boom(self, document, content_hash, original_filename, sample_key=None):  # type: ignore[no-untyped-def]
        raise AppError(
            "LLM_MALFORMED_RESPONSE",
            "The extraction provider returned a response that did not match the schema.",
            502,
        )

    with patch.object(OpenAICompatibleProvider, "extract", boom):
        uploaded = client.post(
            "/api/v1/documents",
            files={"file": (sample_pdf.name, sample_pdf.read_bytes(), "application/pdf")},
        ).json()
        response = client.post(f"/api/v1/documents/{uploaded['id']}/process")

    get_settings.cache_clear()
    monkeypatch.setenv("EXTRACTION_PROVIDER", "fixture")
    assert response.status_code == 502
    document = client.get(f"/api/v1/documents/{uploaded['id']}").json()
    assert document["processing_status"] == "failed"


def test_uploaded_filename_cannot_select_fixture(client, tmp_path: Path) -> None:
    import fitz

    path = tmp_path / "sample_lease.pdf"
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "This is an unrelated office memo, not a Harborpoint sample.")
    pdf.save(path)
    pdf.close()
    processed = process_pdf(client, path)
    lease = client.get(f"/api/v1/leases/{processed['lease_id']}").json()
    assert lease["tenant_name"] is None
    assert lease["approval_source"] is None


def test_processing_failure_is_visible(client, sample_pdf: Path) -> None:
    uploaded = client.post(
        "/api/v1/documents",
        files={"file": (sample_pdf.name, sample_pdf.read_bytes(), "application/pdf")},
    ).json()
    Path(client.app.dependency_overrides and ".")  # keep fixture imported
    from app.db.session import SessionLocal
    from app.models.document import Document

    db = SessionLocal()
    try:
        document = db.get(Document, uploaded["id"])
        assert document is not None
        document.storage_path = str(Path("missing-file.pdf"))
        db.commit()
    finally:
        db.close()

    response = client.post(f"/api/v1/documents/{uploaded['id']}/process")
    assert response.status_code in {422, 500}
    document = client.get(f"/api/v1/documents/{uploaded['id']}").json()
    assert document["processing_status"] == "failed"
    assert document["processing_error"]
