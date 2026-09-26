from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import db_session, settings_dep
from app.core.config import Settings
from app.core.errors import AppError
from app.schemas.common import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


def _wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept.split(",")[0]


def _status_page(title: str, rows: dict[str, str]) -> str:
    items = "".join(
        f"<tr><th scope='row'>{label}</th><td>{value}</td></tr>" for label, value in rows.items()
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: Segoe UI, sans-serif; margin: 2rem; color: #152943; }}
    table {{ border-collapse: collapse; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 0.5rem 0.75rem; text-align: left; }}
    a {{ color: #1e3a5f; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <table><tbody>{items}</tbody></table>
  <p><a href="/docs">OpenAPI docs</a> · <a href="http://localhost:3000">Review UI</a></p>
</body>
</html>"""


@router.get("/health")
def health(request: Request, settings: Settings = Depends(settings_dep)):
    payload = HealthResponse(
        status="ok",
        service=settings.app_name,
        extraction_provider=settings.extraction_provider,
    )
    if _wants_html(request):
        return HTMLResponse(
            _status_page(
                "LeaseFlow AI health",
                {
                    "Status": payload.status,
                    "Service": payload.service,
                    "Extraction provider": payload.extraction_provider,
                },
            )
        )
    return payload


@router.get("/ready")
def ready(request: Request, db: Session = Depends(db_session)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise AppError("NOT_READY", "Database is not reachable.", status_code=503) from exc
    payload = ReadyResponse(status="ok", database="ok")
    if _wants_html(request):
        return HTMLResponse(
            _status_page("LeaseFlow AI readiness", {"Status": payload.status, "Database": payload.database})
        )
    return payload
