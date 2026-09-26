from sqlalchemy import inspect

from app.db import session as session_module


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["extraction_provider"] == "fixture"
    assert "X-Correlation-ID" in response.headers


def test_ready(client) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_schema_initialized(client) -> None:
    tables = set(inspect(session_module.engine).get_table_names())
    assert {
        "documents",
        "leases",
        "extractions",
        "field_evidence",
        "validation_issues",
        "audit_events",
        "export_events",
    }.issubset(tables)
