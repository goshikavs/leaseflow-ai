from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.ids import new_id
from app.domain import FLAG_KEYS
from app.models.feature_flag import FeatureFlag
from app.services.time import utcnow

DEFAULTS: dict[str, bool] = {
    "ENABLE_RAG": True,
    "ENABLE_MCP_CONTEXT": True,
    "ENABLE_MULTI_AGENT": True,
    "ENABLE_PARALLEL_ANALYSIS": True,
    "ENABLE_AI_RECOMMENDATION": True,
    "ENABLE_AUTO_APPROVAL": True,
    "REQUIRE_MANUAL_APPROVAL": False,
    "ENABLE_DOCUMENT_AGENT": True,
    "ENABLE_LEASE_RAG_AGENT": True,
    "ENABLE_PROPERTY_AGENT": True,
    "ENABLE_FINANCE_AGENT": True,
    "ENABLE_LEGAL_AGENT": True,
    "ENABLE_LEASING_AGENT": True,
    "ENABLE_RISK_AGENT": True,
    "ENABLE_RECOMMENDATION_AGENT": True,
    "ENABLE_INSURANCE_AGENT": False,
}

ORG_CEILING: dict[str, bool] = {
    "ENABLE_AUTO_APPROVAL": True,
}

PROPERTY_DEFAULTS: dict[str, dict[str, bool]] = {
    "prop-prosper-retail": {"ENABLE_AUTO_APPROVAL": True, "REQUIRE_MANUAL_APPROVAL": False},
    "prop-dallas-plaza": {"ENABLE_AUTO_APPROVAL": False, "REQUIRE_MANUAL_APPROVAL": True},
    "prop-ntx-logistics": {"ENABLE_AUTO_APPROVAL": False, "REQUIRE_MANUAL_APPROVAL": False},
}


def _rows(db: Session, scope_type: str, scope_id: str) -> dict[str, FeatureFlag]:
    return {
        row.flag_key: row
        for row in db.scalars(
            select(FeatureFlag).where(FeatureFlag.scope_type == scope_type, FeatureFlag.scope_id == scope_id)
        )
    }


def seed_default_flags(db: Session) -> None:
    now = utcnow()
    scopes = [("global", "global"), ("organization", "org-harborpoint")]
    scopes.extend(("property", property_id) for property_id in PROPERTY_DEFAULTS)
    for scope_type, scope_id in scopes:
        existing = _rows(db, scope_type, scope_id)
        values = dict(DEFAULTS)
        if scope_type == "organization":
            values.update(ORG_CEILING)
        if scope_type == "property":
            values.update(PROPERTY_DEFAULTS.get(scope_id, {}))
        for key, enabled in values.items():
            if key in existing:
                continue
            db.add(
                FeatureFlag(
                    id=new_id(),
                    scope_type=scope_type,
                    scope_id=scope_id,
                    flag_key=key,
                    enabled=enabled,
                    config_version=1,
                    updated_at=now,
                )
            )
    db.flush()


def effective_flags(
    db: Session,
    organization_id: str,
    property_id: str,
    *,
    kill_switch: bool = False,
) -> dict[str, bool]:
    seed_default_flags(db)
    resolved = dict(DEFAULTS)
    for scope_type, scope_id in (
        ("global", "global"),
        ("organization", organization_id),
        ("property", property_id),
    ):
        for key, row in _rows(db, scope_type, scope_id).items():
            if scope_type == "property" and key == "ENABLE_AUTO_APPROVAL":
                org_allows = _rows(db, "organization", organization_id).get(key)
                global_allows = _rows(db, "global", "global").get(key)
                if (org_allows and not org_allows.enabled) or (global_allows and not global_allows.enabled):
                    resolved[key] = False
                    continue
            if scope_type == "property" and key == "REQUIRE_MANUAL_APPROVAL":
                org_requires = _rows(db, "organization", organization_id).get(key)
                if org_requires and org_requires.enabled:
                    resolved[key] = True
                    continue
            resolved[key] = row.enabled
    if kill_switch:
        resolved["ENABLE_AUTO_APPROVAL"] = False
    return {key: resolved.get(key, False) for key in FLAG_KEYS}


def flag_version(db: Session, organization_id: str, property_id: str) -> int:
    rows = list(db.scalars(select(FeatureFlag)))
    scoped = [
        row
        for row in rows
        if (row.scope_type, row.scope_id)
        in {("global", "global"), ("organization", organization_id), ("property", property_id)}
    ]
    return max((row.config_version for row in scoped), default=1)
