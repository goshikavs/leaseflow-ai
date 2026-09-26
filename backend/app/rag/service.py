from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.ids import new_id
from app.extraction.schemas import ParsedDocument
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.rag.chunking import chunk_document
from app.rag.embeddings import cosine_similarity, get_embedding_provider
from app.rag.schemas import RagAskResponse, RetrievedChunk
from app.services.time import utcnow


def index_document(
    db: Session,
    document: Document,
    parsed: ParsedDocument,
    *,
    lease_id: str | None,
    target_tokens: int,
    overlap_tokens: int,
) -> list[DocumentChunk]:
    provider = get_embedding_provider()
    prepared = chunk_document(parsed, target_tokens=target_tokens, overlap_tokens=overlap_tokens)
    existing = {
        item.content_hash
        for item in db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document.id))
    }
    created: list[DocumentChunk] = []
    vectors = provider.embed([item.source_text for item in prepared]) if prepared else []
    for item, vector in zip(prepared, vectors, strict=True):
        if item.content_hash in existing:
            continue
        row = DocumentChunk(
            id=new_id(),
            document_id=document.id,
            lease_id=lease_id,
            organization_id=document.organization_id,
            property_id=document.property_id,
            document_version=document.document_version,
            document_type=document.document_type,
            chunk_ordinal=item.ordinal,
            section_heading=item.section_heading,
            start_page=item.start_page,
            end_page=item.end_page,
            source_text=item.source_text,
            content_hash=item.content_hash,
            embedding=vector,
            embedding_model=provider.name,
            embedding_version=provider.version,
            embedding_dimensions=provider.dimensions,
            created_at=utcnow(),
        )
        db.add(row)
        created.append(row)
        existing.add(item.content_hash)
    db.flush()
    return created


def search_chunks(
    db: Session,
    query: str,
    *,
    organization_id: str,
    property_ids: list[str],
    lease_id: str | None = None,
    document_version: int | None = None,
    document_type: str | None = None,
    limit: int = 6,
    min_score: float = 0.12,
) -> list[RetrievedChunk]:
    if not property_ids:
        return []
    provider = get_embedding_provider()
    query_vector = provider.embed([query])[0]
    statement = select(DocumentChunk).where(
        DocumentChunk.organization_id == organization_id,
        DocumentChunk.property_id.in_(property_ids),
    )
    if lease_id:
        statement = statement.where(DocumentChunk.lease_id == lease_id)
    if document_version is not None:
        statement = statement.where(DocumentChunk.document_version == document_version)
    if document_type:
        statement = statement.where(DocumentChunk.document_type == document_type)
    scored: list[RetrievedChunk] = []
    for chunk in db.scalars(statement):
        score = cosine_similarity(query_vector, list(chunk.embedding))
        if score < min_score:
            continue
        scored.append(
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                lease_id=chunk.lease_id,
                organization_id=chunk.organization_id,
                property_id=chunk.property_id,
                document_version=chunk.document_version,
                document_type=chunk.document_type,
                section_heading=chunk.section_heading,
                start_page=chunk.start_page,
                end_page=chunk.end_page,
                source_text=chunk.source_text,
                score=round(score, 4),
            )
        )
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:limit]


def answer_from_chunks(question: str, chunks: list[RetrievedChunk]) -> RagAskResponse:
    provider = get_embedding_provider()
    if not chunks:
        return RagAskResponse(
            answer="The available lease evidence is insufficient to answer that question.",
            insufficient_evidence=True,
            citations=[],
            provider=provider.name,
            model_name=f"{provider.name}-{provider.version}",
        )
    excerpts = []
    for chunk in chunks[:3]:
        excerpt = chunk.source_text.replace("\n", " ")
        excerpts.append(f"{excerpt[:280]} (p.{chunk.start_page}-{chunk.end_page}, {chunk.section_heading})")
    answer = (
        f"Based only on retrieved lease passages: {excerpts[0]} "
        f"Additional supporting text appears in {len(chunks)} chunk(s)."
    )
    if question.lower() and not any(token in chunks[0].source_text.lower() for token in question.lower().split()[:3]):
        # Still grounded: we return retrieved evidence even when lexical overlap is low.
        answer = f"Retrieved lease evidence related to the question: {excerpts[0]}"
    return RagAskResponse(
        answer=answer[:1200],
        insufficient_evidence=False,
        citations=chunks,
        provider=provider.name,
        model_name=f"{provider.name}-{provider.version}",
    )


def detect_amendment_conflicts(db: Session, organization_id: str, property_id: str) -> list[dict]:
    originals = list(
        db.scalars(
            select(DocumentChunk).where(
                DocumentChunk.organization_id == organization_id,
                DocumentChunk.property_id == property_id,
                DocumentChunk.document_type == "lease",
            )
        )
    )
    amendments = list(
        db.scalars(
            select(DocumentChunk).where(
                DocumentChunk.organization_id == organization_id,
                DocumentChunk.property_id == property_id,
                DocumentChunk.document_type == "amendment",
            )
        )
    )
    conflicts = []
    markers = ("rent", "commencement", "expiration", "termination")
    for amendment in amendments:
        for original in originals:
            if amendment.start_page and any(marker in amendment.source_text.lower() for marker in markers):
                if any(marker in original.source_text.lower() for marker in markers):
                    if amendment.source_text != original.source_text and (
                        "increase" in amendment.source_text.lower()
                        or "supersede" in amendment.source_text.lower()
                        or "conflict" in amendment.source_text.lower()
                    ):
                        conflicts.append(
                            {
                                "original_chunk_id": original.id,
                                "amendment_chunk_id": amendment.id,
                                "section": amendment.section_heading,
                                "original_pages": [original.start_page, original.end_page],
                                "amendment_pages": [amendment.start_page, amendment.end_page],
                            }
                        )
                        break
    return conflicts
