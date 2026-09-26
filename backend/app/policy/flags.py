from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ValidationAppError
from app.core.ids import new_id
from app.domain import DEFAULT_LEASE_TYPE, FLAG_KEYS, LEASE_TYPES
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

LEASE_TYPE_DEFAULTS: dict[str, dict[str, bool]] = {
    "commercial": {},
    "residential": {
        "ENABLE_AUTO_APPROVAL": False,
        "REQUIRE_MANUAL_APPROVAL": True,
        "ENABLE_LEASING_AGENT": False,
        "ENABLE_INSURANCE_AGENT": True,
    },
}

AGENT_TOGGLE_KEYS = (
    "ENABLE_DOCUMENT_AGENT",
    "ENABLE_LEASE_RAG_AGENT",
    "ENABLE_PROPERTY_AGENT",
    "ENABLE_FINANCE_AGENT",
    "ENABLE_LEGAL_AGENT",
    "ENABLE_LEASING_AGENT",
    "ENABLE_INSURANCE_AGENT",
    "ENABLE_RISK_AGENT",
    "ENABLE_RECOMMENDATION_AGENT",
)

TIGHTEN_ENABLE_KEYS = {
    "ENABLE_DOCUMENT_AGENT",
    "ENABLE_LEASE_RAG_AGENT",
    "ENABLE_PROPERTY_AGENT",
    "ENABLE_FINANCE_AGENT",
    "ENABLE_LEGAL_AGENT",
    "ENABLE_LEASING_AGENT",
    "ENABLE_RISK_AGENT",
    "ENABLE_RAG",
    "ENABLE_MCP_CONTEXT",
    "ENABLE_MULTI_AGENT",
    "ENABLE_PARALLEL_ANALYSIS",
    "ENABLE_AI_RECOMMENDATION",
    "ENABLE_AUTO_APPROVAL",
}

AGENT_CATALOG = (
    {
        "key": "ENABLE_DOCUMENT_AGENT",
        "agent_name": "document",
        "label": "Document",
        "mandatory": True,
        "description": "Reads extracted fields and indexed chunk counts.",
    },
    {
        "key": "ENABLE_LEASE_RAG_AGENT",
        "agent_name": "lease_rag",
        "label": "Lease RAG",
        "mandatory": True,
        "description": "Retrieves scoped lease passages and amendment conflicts.",
    },
    {
        "key": "ENABLE_PROPERTY_AGENT",
        "agent_name": "property",
        "label": "Property",
        "mandatory": True,
        "description": "Looks up property profile and maintenance status.",
    },
    {
        "key": "ENABLE_FINANCE_AGENT",
        "agent_name": "finance",
        "label": "Finance",
        "mandatory": True,
        "description": "Checks tenant financial status and rent ceilings.",
    },
    {
        "key": "ENABLE_LEGAL_AGENT",
        "agent_name": "legal",
        "label": "Legal",
        "mandatory": True,
        "description": "Reads legal review status and clause templates.",
    },
    {
        "key": "ENABLE_LEASING_AGENT",
        "agent_name": "leasing",
        "label": "Leasing",
        "mandatory": True,
        "description": "Reads negotiation status and approved rent.",
    },
    {
        "key": "ENABLE_INSURANCE_AGENT",
        "agent_name": "insurance",
        "label": "Insurance",
        "mandatory": False,
        "description": "Optional insurance-compliance specialist.",
    },
    {
        "key": "ENABLE_RISK_AGENT",
        "agent_name": "risk",
        "label": "Risk",
        "mandatory": True,
        "description": "Aggregates specialist failures before policy.",
    },
    {
        "key": "ENABLE_RECOMMENDATION_AGENT",
        "agent_name": "recommendation",
        "label": "Recommendation",
        "mandatory": False,
        "description": "Advisory only. Policy remains authoritative.",
    },
)


def normalize_lease_type(value: str | None) -> str:
    candidate = (value or DEFAULT_LEASE_TYPE).strip().lower()
    return candidate if candidate in LEASE_TYPES else DEFAULT_LEASE_TYPE


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
    scopes.extend(("lease_type", lease_type) for lease_type in LEASE_TYPES)
    for scope_type, scope_id in scopes:
        existing = _rows(db, scope_type, scope_id)
        if scope_type == "property":
            values = dict(PROPERTY_DEFAULTS.get(scope_id, {}))
        else:
            values = dict(DEFAULTS)
            if scope_type == "organization":
                values.update(ORG_CEILING)
            if scope_type == "lease_type":
                values.update(LEASE_TYPE_DEFAULTS.get(scope_id, {}))
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
    lease_type: str | None = None,
    kill_switch: bool = False,
) -> dict[str, bool]:
    normalized_type = normalize_lease_type(lease_type)
    seed_default_flags(db)
    resolved = dict(DEFAULTS)
    for scope_type, scope_id in (
        ("global", "global"),
        ("organization", organization_id),
        ("lease_type", normalized_type),
        ("property", property_id),
    ):
        for key, row in _rows(db, scope_type, scope_id).items():
            if key not in FLAG_KEYS:
                continue
            if scope_type == "property" and key in AGENT_TOGGLE_KEYS:
                continue
            if scope_type in {"lease_type", "property"}:
                if key in TIGHTEN_ENABLE_KEYS and row.enabled and not resolved.get(key, False):
                    continue
                if key == "REQUIRE_MANUAL_APPROVAL" and resolved.get(key) and not row.enabled:
                    continue
            resolved[key] = row.enabled
    if kill_switch:
        resolved["ENABLE_AUTO_APPROVAL"] = False
    return {key: resolved.get(key, False) for key in FLAG_KEYS}


def flag_version(
    db: Session,
    organization_id: str,
    property_id: str,
    *,
    lease_type: str | None = None,
) -> int:
    normalized_type = normalize_lease_type(lease_type)
    rows = list(db.scalars(select(FeatureFlag)))
    scoped = [
        row
        for row in rows
        if (row.scope_type, row.scope_id)
        in {
            ("global", "global"),
            ("organization", organization_id),
            ("lease_type", normalized_type),
            ("property", property_id),
        }
    ]
    return max((row.config_version for row in scoped), default=1)


def lease_type_agent_flags(db: Session, lease_type: str) -> dict[str, bool]:
    normalized_type = normalize_lease_type(lease_type)
    seed_default_flags(db)
    rows = _rows(db, "lease_type", normalized_type)
    configured = dict(DEFAULTS)
    configured.update(LEASE_TYPE_DEFAULTS.get(normalized_type, {}))
    return {key: rows[key].enabled if key in rows else configured[key] for key in AGENT_TOGGLE_KEYS}


def update_lease_type_flags(db: Session, lease_type: str, updates: dict[str, bool]) -> dict[str, bool]:
    normalized_type = normalize_lease_type(lease_type)
    if lease_type and lease_type.strip().lower() not in LEASE_TYPES:
        raise ValidationAppError("Lease type must be commercial or residential.", code="INVALID_LEASE_TYPE")
    unknown = sorted(key for key in updates if key not in AGENT_TOGGLE_KEYS)
    if unknown:
        raise ValidationAppError(
            "Only specialist-agent flags can be updated for a lease type.",
            code="INVALID_AGENT_FLAG",
            details=[{"flag_key": key} for key in unknown],
        )
    seed_default_flags(db)
    now = utcnow()
    existing = _rows(db, "lease_type", normalized_type)
    for key, enabled in updates.items():
        row = existing.get(key)
        if row is None:
            db.add(
                FeatureFlag(
                    id=new_id(),
                    scope_type="lease_type",
                    scope_id=normalized_type,
                    flag_key=key,
                    enabled=enabled,
                    config_version=1,
                    updated_at=now,
                )
            )
        else:
            row.enabled = enabled
            row.config_version += 1
            row.updated_at = now
    db.flush()
    return lease_type_agent_flags(db, normalized_type)


def lease_type_catalog(db: Session) -> dict[str, object]:
    seed_default_flags(db)
    return {
        "lease_types": [
            {
                "lease_type": lease_type,
                "label": lease_type.title(),
                "description": (
                    "Office, retail, and industrial leases in the Harborpoint demo."
                    if lease_type == "commercial"
                    else "Residential leases. Auto-approval stays off unless a higher policy already blocked it."
                ),
                "flags": lease_type_agent_flags(db, lease_type),
            }
            for lease_type in LEASE_TYPES
        ],
        "agents": list(AGENT_CATALOG),
        "note": (
            "Lease-type settings cannot turn on an agent that the organization disabled. "
            "Disabling a required agent skips that specialist and blocks auto-approval."
        ),
    }
