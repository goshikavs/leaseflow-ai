from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal


def db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def settings_dep() -> Settings:
    return get_settings()


def actor_dep(settings: Settings = None) -> str:  # type: ignore[assignment]
    if settings is None:
        settings = get_settings()
    return settings.demo_actor


def correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "")
