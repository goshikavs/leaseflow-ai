from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session, settings_dep
from app.core.config import Settings
from app.schemas.common import Page
from app.schemas.export import ApprovedLeaseExport
from app.schemas.lease import (
    ApproveRequest,
    AuditEventOut,
    LeaseDetail,
    LeaseSummary,
    LeaseUpdate,
)
from app.services.leases import (
    approve_lease,
    export_lease,
    get_lease,
    list_audit_events,
    list_leases,
    to_detail,
    to_summary,
    update_lease,
)

router = APIRouter(prefix="/api/v1/leases", tags=["leases"])


@router.get("", response_model=Page[LeaseSummary])
def get_leases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    db: Session = Depends(db_session),
) -> Page[LeaseSummary]:
    items, total = list_leases(db, page, page_size, status)
    return Page(
        items=[to_summary(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{lease_id}", response_model=LeaseDetail)
def get_lease_detail(
    lease_id: str,
    db: Session = Depends(db_session),
    settings: Settings = Depends(settings_dep),
) -> LeaseDetail:
    return to_detail(get_lease(db, lease_id), settings.extraction_provider == "fixture")


@router.patch("/{lease_id}", response_model=LeaseDetail)
def patch_lease(
    lease_id: str,
    payload: LeaseUpdate,
    db: Session = Depends(db_session),
    settings: Settings = Depends(settings_dep),
) -> LeaseDetail:
    lease = update_lease(db, get_lease(db, lease_id), payload, settings.demo_actor)
    return to_detail(lease, settings.extraction_provider == "fixture")


@router.post("/{lease_id}/approve", response_model=LeaseDetail)
def post_approve(
    lease_id: str,
    payload: ApproveRequest,
    db: Session = Depends(db_session),
    settings: Settings = Depends(settings_dep),
) -> LeaseDetail:
    lease = approve_lease(db, get_lease(db, lease_id), payload, settings.demo_actor)
    return to_detail(lease, settings.extraction_provider == "fixture")


@router.get("/{lease_id}/export", response_model=ApprovedLeaseExport)
def get_export(
    lease_id: str,
    db: Session = Depends(db_session),
    settings: Settings = Depends(settings_dep),
) -> ApprovedLeaseExport:
    return export_lease(db, get_lease(db, lease_id), settings.demo_actor)


@router.get("/{lease_id}/audit", response_model=list[AuditEventOut])
def get_audit(
    lease_id: str,
    db: Session = Depends(db_session),
) -> list[AuditEventOut]:
    return list_audit_events(get_lease(db, lease_id))
