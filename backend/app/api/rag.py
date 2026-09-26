from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import db_session, settings_dep
from app.core.config import Settings
from app.core.errors import AppError
from app.rag.schemas import RagAskResponse, RagSearchResponse
from app.rag.service import answer_from_chunks, search_chunks

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


class RagQuery(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    organization_id: str
    property_ids: list[str] = Field(min_length=1)
    lease_id: str | None = None
    document_version: int | None = None
    document_type: str | None = None
    limit: int = Field(default=6, ge=1, le=20)


def _authorized_org(
    organization_id: str,
    x_organization_id: str | None,
    settings: Settings,
) -> str:
    requested = (x_organization_id or settings.default_organization_id).strip()
    if organization_id != requested:
        raise AppError("ORG_SCOPE_DENIED", "Cross-organization retrieval is not permitted.", status_code=403)
    return requested


@router.post("/search", response_model=RagSearchResponse)
def rag_search(
    payload: RagQuery,
    db: Session = Depends(db_session),
    settings: Settings = Depends(settings_dep),
    x_organization_id: str | None = Header(default=None),
) -> RagSearchResponse:
    org = _authorized_org(payload.organization_id, x_organization_id, settings)
    items = search_chunks(
        db,
        payload.query,
        organization_id=org,
        property_ids=payload.property_ids,
        lease_id=payload.lease_id,
        document_version=payload.document_version,
        document_type=payload.document_type,
        limit=payload.limit,
        min_score=settings.rag_min_score,
    )
    return RagSearchResponse(items=items)


@router.post("/ask", response_model=RagAskResponse)
def rag_ask(
    payload: RagQuery,
    db: Session = Depends(db_session),
    settings: Settings = Depends(settings_dep),
    x_organization_id: str | None = Header(default=None),
) -> RagAskResponse:
    org = _authorized_org(payload.organization_id, x_organization_id, settings)
    chunks = search_chunks(
        db,
        payload.query,
        organization_id=org,
        property_ids=payload.property_ids,
        lease_id=payload.lease_id,
        document_version=payload.document_version,
        document_type=payload.document_type,
        limit=payload.limit,
        min_score=settings.rag_min_score,
    )
    return answer_from_chunks(payload.query, chunks)
