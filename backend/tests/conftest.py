from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import db_session
from app.core.config import get_settings
from app.db import session as session_module
from app.main import app

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "test.db"
    storage = tmp_path / "uploads"
    storage.mkdir()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("STORAGE_DIR", str(storage))
    monkeypatch.setenv("EXTRACTION_PROVIDER", "fixture")
    monkeypatch.setenv("SAMPLES_DIR", str(SAMPLES_DIR))
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    get_settings.cache_clear()
    settings = get_settings()

    engine = create_engine(
        settings.sqlalchemy_database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _fk(dbapi_connection, _record):  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session_module.engine = engine
    session_module.SessionLocal = TestingSession

    def override_db() -> Generator:
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_session] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest.fixture
def sample_pdf() -> Path:
    path = SAMPLES_DIR / "sample_lease.pdf"
    if not path.exists():
        pytest.skip("Sample PDFs have not been generated")
    return path


@pytest.fixture
def missing_pdf() -> Path:
    path = SAMPLES_DIR / "missing_fields_lease.pdf"
    if not path.exists():
        pytest.skip("Sample PDFs have not been generated")
    return path


@pytest.fixture
def conflicting_pdf() -> Path:
    path = SAMPLES_DIR / "conflicting_dates_lease.pdf"
    if not path.exists():
        pytest.skip("Sample PDFs have not been generated")
    return path
