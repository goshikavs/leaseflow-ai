from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import db_session, settings_dep
from app.core.config import Settings
from app.core.errors import AppError
from app.schemas.common import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(settings_dep)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        extraction_provider=settings.extraction_provider,
    )


@router.get("/ready", response_model=ReadyResponse)
def ready(db: Session = Depends(db_session)) -> ReadyResponse:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise AppError("NOT_READY", "Database is not reachable.", status_code=503) from exc
    return ReadyResponse(status="ok", database="ok")
