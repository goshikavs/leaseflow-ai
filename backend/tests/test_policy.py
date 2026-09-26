from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.ids import new_id
from app.domain import DEMO_ORG_ID, PROPERTY_DALLAS, PROPERTY_LOGISTICS, PROPERTY_PROSPER
from app.models.feature_flag import FeatureFlag
from app.policy.engine import (
    AUTO_APPROVED,
    BLOCKED,
    ESCALATED,
    MANUAL_REVIEW_REQUIRED,
    PolicyInput,
    evaluate_policy,
)
from app.policy.flags import DEFAULTS, effective_flags, seed_default_flags
from app.services.time import utcnow


def _base(**overrides: object) -> PolicyInput:
    payload = {
        "organization_id": DEMO_ORG_ID,
        "property_id": PROPERTY_PROSPER,
        "flags": {**DEFAULTS, "REQUIRE_MANUAL_APPROVAL": False, "ENABLE_AUTO_APPROVAL": True},
        "policy_version": 1,
        "lease_version": 1,
        "monthly_base_rent": Decimal("4200.00"),
    }
    payload.update(overrides)
    return PolicyInput.model_validate(payload)


def test_prosper_eligible_auto_approval() -> None:
    result = evaluate_policy(_base())
    assert result.decision == AUTO_APPROVED
    assert "PROSPER_POLICY_PASS" in result.reason_codes


def test_dallas_always_manual() -> None:
    result = evaluate_policy(_base(property_id=PROPERTY_DALLAS, monthly_base_rent=Decimal("78000.00")))
    assert result.decision == MANUAL_REVIEW_REQUIRED
    assert "DALLAS_MANUAL_REVIEW" in result.reason_codes


def test_logistics_conflict_escalates() -> None:
    result = evaluate_policy(
        _base(property_id=PROPERTY_LOGISTICS, has_amendment_conflict=True, monthly_base_rent=Decimal("31500.00"))
    )
    assert result.decision == ESCALATED
    assert "AMENDMENT_CONFLICT" in result.reason_codes


def test_fail_closed_cases() -> None:
    assert evaluate_policy(_base(kill_switch=True)).decision == BLOCKED
    assert evaluate_policy(_base(evidence_complete=False)).decision == BLOCKED
    assert evaluate_policy(_base(mandatory_agents_ok=False)).decision == BLOCKED
    assert evaluate_policy(_base(required_tools_ok=False)).decision == BLOCKED
    assert evaluate_policy(_base(has_blocking_issues=True)).decision == BLOCKED
    assert evaluate_policy(_base(expected_lease_version=2)).decision == BLOCKED
    assert evaluate_policy(_base(stale_context=True)).decision == BLOCKED
    legal = evaluate_policy(
        _base(
            property_id=PROPERTY_LOGISTICS,
            legal_exceptions=["open"],
            monthly_base_rent=Decimal("31500"),
        )
    )
    assert legal.decision == ESCALATED


def test_org_restriction_cannot_be_loosened_by_property(client) -> None:
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        seed_default_flags(db)
        _set_flag(db, "organization", DEMO_ORG_ID, "ENABLE_AUTO_APPROVAL", False)
        _set_flag(db, "property", PROPERTY_PROSPER, "ENABLE_AUTO_APPROVAL", True)
        flags = effective_flags(db, DEMO_ORG_ID, PROPERTY_PROSPER)
        assert flags["ENABLE_AUTO_APPROVAL"] is False
        _set_flag(db, "organization", DEMO_ORG_ID, "REQUIRE_MANUAL_APPROVAL", True)
        _set_flag(db, "property", PROPERTY_PROSPER, "REQUIRE_MANUAL_APPROVAL", False)
        flags = effective_flags(db, DEMO_ORG_ID, PROPERTY_PROSPER)
        assert flags["REQUIRE_MANUAL_APPROVAL"] is True
        db.commit()
    finally:
        db.close()


def test_kill_switch_and_effective_api(client) -> None:
    response = client.get(
        "/api/v1/flags/effective",
        params={"organization_id": DEMO_ORG_ID, "property_id": PROPERTY_DALLAS},
        headers={"X-Organization-ID": DEMO_ORG_ID},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["restricted"] is True
    assert body["flags"]["REQUIRE_MANUAL_APPROVAL"] is True
    denied = client.get(
        "/api/v1/flags/effective",
        params={"organization_id": "org-other", "property_id": PROPERTY_DALLAS},
        headers={"X-Organization-ID": DEMO_ORG_ID},
    )
    assert denied.status_code == 403


def _set_flag(db: Session, scope_type: str, scope_id: str, key: str, enabled: bool) -> None:
    row = db.scalar(
        select(FeatureFlag).where(
            FeatureFlag.scope_type == scope_type,
            FeatureFlag.scope_id == scope_id,
            FeatureFlag.flag_key == key,
        )
    )
    if row is None:
        db.add(
            FeatureFlag(
                id=new_id(),
                scope_type=scope_type,
                scope_id=scope_id,
                flag_key=key,
                enabled=enabled,
                config_version=2,
                updated_at=utcnow(),
            )
        )
    else:
        row.enabled = enabled
        row.config_version += 1
        row.updated_at = utcnow()
    db.flush()
