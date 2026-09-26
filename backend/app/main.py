from pathlib import Path
from uuid import uuid4

from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from alembic import command
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.leases import router as leases_router
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.models import (  # noqa: F401
    audit_event,
    document,
    export_event,
    extraction,
    field_evidence,
    lease,
    validation_issue,
)

configure_logging()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "AI-assisted commercial lease extraction, validation, human review, "
        "and versioned export. This demo does not provide legal advice."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
)


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


def _error_payload(code: str, message: str, correlation_id: str | None, details: list | None = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "correlation_id": correlation_id,
        }
    }


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(exc.code, exc.message, correlation_id, exc.details),
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    details = [
        {
            "field": ".".join(str(part) for part in err.get("loc", [])),
            "message": err.get("msg"),
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=_error_payload("REQUEST_VALIDATION_ERROR", "Request validation failed.", correlation_id, details),
    )


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, _exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    return JSONResponse(
        status_code=500,
        content=_error_payload("INTERNAL_ERROR", "An unexpected error occurred.", correlation_id),
    )


app.include_router(health_router)
app.include_router(documents_router)
app.include_router(leases_router)


@app.get("/", include_in_schema=False)
def root() -> HTMLResponse:
    return HTMLResponse(
        """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>LeaseFlow AI API</title>
  <style>
    body { font-family: Segoe UI, sans-serif; margin: 2rem; color: #152943; max-width: 40rem; }
    a { color: #1e3a5f; }
    code { background: #f1f5f9; padding: 0.1rem 0.35rem; }
  </style>
</head>
<body>
  <h1>LeaseFlow AI API</h1>
  <p>This is the backend on port 8000. It serves JSON APIs, not the review screens.</p>
  <ul>
    <li><a href="http://localhost:3000">Open the review UI</a> (port 3000)</li>
    <li><a href="/docs">OpenAPI documentation</a></li>
    <li><a href="/health">Health check</a></li>
  </ul>
</body>
</html>"""
    )


@app.on_event("startup")
def startup() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", get_settings().sqlalchemy_database_url)
    command.upgrade(config, "head")
