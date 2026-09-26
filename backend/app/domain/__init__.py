"""Domain constants for the demo organization and properties."""

DEMO_ORG_ID = "org-harborpoint"

PROPERTY_PROSPER = "prop-prosper-retail"
PROPERTY_DALLAS = "prop-dallas-plaza"
PROPERTY_LOGISTICS = "prop-ntx-logistics"

PROPERTY_CATALOG = {
    PROPERTY_PROSPER: {
        "name": "Prosper Retail Center",
        "property_type": "retail",
        "address": "100 Prosper Crossing, Prosper, TX 75078",
        "tenant": "Northstar Coffee LLC",
        "monthly_base_rent": "4200.00",
    },
    PROPERTY_DALLAS: {
        "name": "Dallas Corporate Plaza",
        "property_type": "office",
        "address": "2200 Ross Avenue, Suite 1800, Dallas, TX 75201",
        "tenant": "Atlas Technology Services LLC",
        "monthly_base_rent": "78000.00",
    },
    PROPERTY_LOGISTICS: {
        "name": "North Texas Logistics Park",
        "property_type": "industrial",
        "address": "4800 Belt Line Road, Building 7, Irving, TX 75038",
        "tenant": "Meridian Distribution LLC",
        "monthly_base_rent": "31500.00",
    },
}

FLAG_KEYS = (
    "ENABLE_RAG",
    "ENABLE_MCP_CONTEXT",
    "ENABLE_MULTI_AGENT",
    "ENABLE_PARALLEL_ANALYSIS",
    "ENABLE_AI_RECOMMENDATION",
    "ENABLE_AUTO_APPROVAL",
    "REQUIRE_MANUAL_APPROVAL",
    "ENABLE_DOCUMENT_AGENT",
    "ENABLE_LEASE_RAG_AGENT",
    "ENABLE_PROPERTY_AGENT",
    "ENABLE_FINANCE_AGENT",
    "ENABLE_LEGAL_AGENT",
    "ENABLE_LEASING_AGENT",
    "ENABLE_RISK_AGENT",
    "ENABLE_RECOMMENDATION_AGENT",
    "ENABLE_INSURANCE_AGENT",
)
