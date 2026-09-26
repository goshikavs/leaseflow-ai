# Data contract

Approved leases export a versioned JSON document. The example in the assignment is illustrative. Live exports use stored lease rows.

## Schema version 1.0

```json
{
  "schema_version": "1.0",
  "source_system": "leaseflow-ai",
  "lease_id": "uuid",
  "tenant": { "name": "Northwind Analytics LLC" },
  "property": { "address": "1200 Commerce Street, Suite 400, Dallas, TX 75201" },
  "financial_terms": {
    "monthly_base_rent": "18500.00",
    "currency": "USD"
  },
  "important_dates": {
    "commencement": "2026-01-01",
    "expiration": "2028-12-31",
    "renewal_notice_days": 180
  },
  "review": {
    "status": "approved",
    "approved_by": "demo-reviewer"
  }
}
```

Rules:

- `monthly_base_rent` is a decimal string with two places, or `null`
- dates are ISO `YYYY-MM-DD` or `null`
- missing values are explicit `null`, not omitted keys
- `schema_version` is `"1.0"` for this release

The Pydantic model `ApprovedLeaseExport` is the executable contract. Backend tests validate both the example shape and a real approved sample.

## Why this is separate from extraction

`extractions.structured_output` stores model or fixture output. The lease table is the system of record after evidence checks and human edits. Consumers should bind to the export contract.

## Future publication

A later integration can POST this JSON to a client API or publish it to a queue. That worker would read approved leases and `export_events`, not call the LLM again. No external property-management system is integrated in this repository.
