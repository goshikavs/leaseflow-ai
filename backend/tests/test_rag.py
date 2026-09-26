from pathlib import Path

from sqlalchemy import func, select

from app.db import session as session_module
from app.extraction.schemas import ParsedDocument, ParsedPage
from app.models.document_chunk import DocumentChunk
from app.rag.chunking import chunk_document
from app.rag.embeddings import LocalHashingEmbeddingProvider, cosine_similarity
from app.rag.service import answer_from_chunks
from tests.helpers import process_pdf

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


def _parsed(pages: list[str]) -> ParsedDocument:
    return ParsedDocument(
        page_count=len(pages),
        pages=[ParsedPage(page_number=index + 1, text=text) for index, text in enumerate(pages)],
    )


def test_chunking_preserves_pages_and_overlap() -> None:
    pages = [f"SECTION RENT PAGE {index} " + ("rent schedule clause " * 80) for index in range(1, 5)]
    chunks = chunk_document(_parsed(pages), target_tokens=80, overlap_tokens=20)
    assert len(chunks) >= 2
    assert chunks[0].start_page == 1
    assert chunks[-1].end_page >= chunks[0].start_page
    first_words = set(chunks[0].source_text.split()[-15:])
    second_words = set(chunks[1].source_text.split()[:15])
    assert first_words.intersection(second_words)


def test_embeddings_are_similar_for_related_text() -> None:
    provider = LocalHashingEmbeddingProvider()
    rent, close, other = provider.embed(
        [
            "Monthly base rent is 4200.00 USD for the retail premises",
            "The coffee tenant pays four thousand two hundred in monthly base rent",
            "Dock scheduling and trailer storage follow the industrial park rules",
        ]
    )
    assert provider.dimensions == 256
    assert cosine_similarity(rent, close) > cosine_similarity(rent, other)
    assert cosine_similarity(rent, rent) > 0.99


def test_vector_search_and_org_isolation(client) -> None:
    path = SAMPLES / "prosper_retail_lease.pdf"
    if not path.exists():
        raise AssertionError("Run samples/generate_samples.py")
    processed = process_pdf(
        client, path, organization_id="org-harborpoint", property_id="prop-prosper-retail"
    )
    search = client.post(
        "/api/v1/rag/search",
        headers={"X-Organization-ID": "org-harborpoint"},
        json={
            "query": "monthly base rent for Northstar Coffee",
            "organization_id": "org-harborpoint",
            "property_ids": ["prop-prosper-retail"],
            "limit": 5,
        },
    )
    assert search.status_code == 200, search.text
    items = search.json()["items"]
    assert items
    assert items[0]["start_page"] >= 1
    assert "4200" in items[0]["source_text"] or "Northstar" in items[0]["source_text"]
    denied = client.post(
        "/api/v1/rag/search",
        headers={"X-Organization-ID": "org-harborpoint"},
        json={
            "query": "monthly base rent",
            "organization_id": "org-other",
            "property_ids": ["prop-prosper-retail"],
        },
    )
    assert denied.status_code == 403
    other = client.post(
        "/api/v1/rag/search",
        headers={"X-Organization-ID": "org-other"},
        json={
            "query": "monthly base rent for Northstar Coffee",
            "organization_id": "org-other",
            "property_ids": ["prop-prosper-retail"],
        },
    )
    assert other.status_code == 200
    assert other.json()["items"] == []
    ask = client.post(
        "/api/v1/rag/ask",
        headers={"X-Organization-ID": "org-harborpoint"},
        json={
            "query": "What is the monthly base rent?",
            "organization_id": "org-harborpoint",
            "property_ids": ["prop-prosper-retail"],
            "lease_id": processed["lease_id"],
        },
    )
    body = ask.json()
    assert ask.status_code == 200
    assert body["insufficient_evidence"] is False
    assert body["citations"]
    missing = answer_from_chunks("unknown clause", [])
    assert missing.insufficient_evidence is True


def test_duplicate_ingestion_is_idempotent(client) -> None:
    path = SAMPLES / "prosper_retail_lease.pdf"
    processed = process_pdf(client, path, organization_id="org-harborpoint", property_id="prop-prosper-retail")
    first = client.post(f"/api/v1/documents/{processed['document']['id']}/process")
    assert first.status_code == 200
    db = session_module.SessionLocal()
    try:
        count = db.scalar(select(func.count()).select_from(DocumentChunk)) or 0
        assert count > 0
        document_id = processed["document"]["id"]
        hashes = list(
            db.scalars(select(DocumentChunk.content_hash).where(DocumentChunk.document_id == document_id))
        )
        assert len(hashes) == len(set(hashes))
    finally:
        db.close()


def test_amendment_conflict_is_surfaced(client) -> None:
    original = SAMPLES / "logistics_park_lease.pdf"
    amendment = SAMPLES / "logistics_park_amendment.pdf"
    if not original.exists():
        raise AssertionError("Run samples/generate_samples.py")
    process_pdf(client, original, organization_id="org-harborpoint", property_id="prop-ntx-logistics")
    process_pdf(
        client,
        amendment,
        organization_id="org-harborpoint",
        property_id="prop-ntx-logistics",
        document_type="amendment",
        document_version=2,
    )
    from app.rag.service import detect_amendment_conflicts

    db = session_module.SessionLocal()
    try:
        conflicts = detect_amendment_conflicts(db, "org-harborpoint", "prop-ntx-logistics")
        assert conflicts
    finally:
        db.close()
