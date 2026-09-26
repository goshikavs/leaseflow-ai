from __future__ import annotations

from app.domain import DEMO_ORG_ID, PROPERTY_DALLAS, PROPERTY_LOGISTICS, PROPERTY_PROSPER

CATALOG = {
    "property": {
        PROPERTY_PROSPER: {
            "organization_id": DEMO_ORG_ID,
            "property_id": PROPERTY_PROSPER,
            "name": "Prosper Retail Center",
            "property_type": "retail",
            "maintenance_status": "current",
            "open_work_orders": 0,
        },
        PROPERTY_DALLAS: {
            "organization_id": DEMO_ORG_ID,
            "property_id": PROPERTY_DALLAS,
            "name": "Dallas Corporate Plaza",
            "property_type": "office",
            "maintenance_status": "scheduled_capital_project",
            "open_work_orders": 2,
        },
        PROPERTY_LOGISTICS: {
            "organization_id": DEMO_ORG_ID,
            "property_id": PROPERTY_LOGISTICS,
            "name": "North Texas Logistics Park",
            "property_type": "industrial",
            "maintenance_status": "current",
            "open_work_orders": 1,
        },
    },
    "finance": {
        PROPERTY_PROSPER: {
            "organization_id": DEMO_ORG_ID,
            "property_id": PROPERTY_PROSPER,
            "tenant_status": "current",
            "delinquent_balance": "0.00",
            "auto_approval_rent_ceiling": "5000.00",
            "threshold_exceeded": False,
        },
        PROPERTY_DALLAS: {
            "organization_id": DEMO_ORG_ID,
            "property_id": PROPERTY_DALLAS,
            "tenant_status": "current",
            "delinquent_balance": "0.00",
            "auto_approval_rent_ceiling": "5000.00",
            "threshold_exceeded": True,
        },
        PROPERTY_LOGISTICS: {
            "organization_id": DEMO_ORG_ID,
            "property_id": PROPERTY_LOGISTICS,
            "tenant_status": "watch",
            "delinquent_balance": "2400.00",
            "auto_approval_rent_ceiling": "5000.00",
            "threshold_exceeded": True,
        },
    },
    "legal": {
        PROPERTY_PROSPER: {
            "organization_id": DEMO_ORG_ID,
            "property_id": PROPERTY_PROSPER,
            "review_status": "cleared",
            "unresolved_exceptions": [],
            "approved_clause_templates": ["retail-base-form-2025"],
        },
        PROPERTY_DALLAS: {
            "organization_id": DEMO_ORG_ID,
            "property_id": PROPERTY_DALLAS,
            "review_status": "in_review",
            "unresolved_exceptions": ["assignment-consent-pending"],
            "approved_clause_templates": ["office-base-form-2025"],
        },
        PROPERTY_LOGISTICS: {
            "organization_id": DEMO_ORG_ID,
            "property_id": PROPERTY_LOGISTICS,
            "review_status": "exception",
            "unresolved_exceptions": ["amendment-conflict-rent"],
            "approved_clause_templates": ["industrial-base-form-2025"],
        },
    },
    "leasing": {
        PROPERTY_PROSPER: {
            "organization_id": DEMO_ORG_ID,
            "property_id": PROPERTY_PROSPER,
            "negotiation_status": "complete",
            "approved_monthly_rent": "4200.00",
            "unresolved_commercial_issues": [],
        },
        PROPERTY_DALLAS: {
            "organization_id": DEMO_ORG_ID,
            "property_id": PROPERTY_DALLAS,
            "negotiation_status": "pending_business_review",
            "approved_monthly_rent": "78000.00",
            "unresolved_commercial_issues": ["capex-allowance"],
        },
        PROPERTY_LOGISTICS: {
            "organization_id": DEMO_ORG_ID,
            "property_id": PROPERTY_LOGISTICS,
            "negotiation_status": "complete",
            "approved_monthly_rent": "31500.00",
            "unresolved_commercial_issues": ["amendment-rent-reset"],
        },
    },
    "insurance": {
        PROPERTY_PROSPER: {
            "organization_id": DEMO_ORG_ID,
            "property_id": PROPERTY_PROSPER,
            "certificate_status": "current",
            "coverage_expiration": "2027-01-01",
            "exceptions": [],
        },
        PROPERTY_DALLAS: {
            "organization_id": DEMO_ORG_ID,
            "property_id": PROPERTY_DALLAS,
            "certificate_status": "current",
            "coverage_expiration": "2026-12-31",
            "exceptions": [],
        },
        PROPERTY_LOGISTICS: {
            "organization_id": DEMO_ORG_ID,
            "property_id": PROPERTY_LOGISTICS,
            "certificate_status": "exception",
            "coverage_expiration": "2026-04-30",
            "exceptions": ["umbrella-limit-below-requirement"],
        },
    },
}

TOOL_ALLOWLIST = {
    "property": {"get_property_profile", "get_property_maintenance_status"},
    "finance": {"get_tenant_financial_status", "get_property_financial_thresholds"},
    "legal": {"get_legal_review_status", "get_approved_clause_templates"},
    "leasing": {"get_leasing_context", "get_lease_negotiation_status"},
    "insurance": {"get_insurance_compliance"},
}
