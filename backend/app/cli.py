"""Idempotent demo seed and RAG verification commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import func, select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.domain import DEMO_ORG_ID, PROPERTY_DALLAS, PROPERTY_LOGISTICS, PROPERTY_PROSPER
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.policy.flags import seed_default_flags
from app.rag.embeddings import get_embedding_provider
from app.rag.service import search_chunks
from app.services.documents import create_document, load_sample_bytes
from app.workflows.processing import process_document

SEED_SPECS = (
    ("prosper_retail_lease", PROPERTY_PROSPER, "lease", 1),
    ("dallas_plaza_lease", PROPERTY_DALLAS, "lease", 1),
    ("logistics_park_lease", PROPERTY_LOGISTICS, "lease", 1),
    ("logistics_park_large", PROPERTY_LOGISTICS, "lease", 1),
    ("logistics_park_amendment", PROPERTY_LOGISTICS, "amendment", 2),
)


def seed() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        seed_default_flags(db)
        for key, property_id, document_type, version in SEED_SPECS:
            filename, data = load_sample_bytes(settings, key)
            existing = db.scalar(
                select(Document).where(
                    Document.original_filename == filename,
                    Document.property_id == property_id,
                    Document.document_type == document_type,
                )
            )
            if existing:
                if existing.processing_status == "uploaded":
                    process_document(db, settings, existing, settings.demo_actor)
                continue
            document = create_document(
                db,
                settings,
                filename,
                data,
                organization_id=DEMO_ORG_ID,
                property_id=property_id,
                document_type=document_type,
                document_version=version,
                sample_key=key,
            )
            process_document(db, settings, document, settings.demo_actor)
        db.commit()
        print(json.dumps(verify(db), indent=2))
    finally:
        db.close()


def verify(db=None) -> dict:
    close = False
    if db is None:
        db = SessionLocal()
        close = True
    try:
        provider = get_embedding_provider()
        documents = db.scalar(select(func.count()).select_from(Document)) or 0
        chunks = db.scalar(select(func.count()).select_from(DocumentChunk)) or 0
        vectors = db.scalar(
            select(func.count()).select_from(DocumentChunk).where(DocumentChunk.embedding.is_not(None))
        ) or 0
        example = [
            {
                "score": item.score,
                "section": item.section_heading,
                "pages": [item.start_page, item.end_page],
                "document_id": item.document_id,
                "excerpt": item.source_text[:180],
            }
            for item in search_chunks(
                db,
                "monthly base rent for Northstar Coffee",
                organization_id=DEMO_ORG_ID,
                property_ids=[PROPERTY_PROSPER],
                limit=3,
                min_score=0.01,
            )
        ]
        return {
            "documents": documents,
            "chunks": chunks,
            "vectors": vectors,
            "embedding_dimensions": provider.dimensions,
            "embedding_model": f"{provider.name}-{provider.version}",
            "example_similarity_search": example,
        }
    finally:
        if close:
            db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="LeaseFlow demo utilities")
    parser.add_argument("command", choices=["seed", "verify-rag"])
    args = parser.parse_args()
    if args.command == "seed":
        if not (Path(__file__).resolve().parents[2] / "samples" / "prosper_retail_lease.pdf").exists():
            raise SystemExit("Run python samples/generate_samples.py first.")
        seed()
        return 0
    print(json.dumps(verify(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
