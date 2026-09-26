# API

FastAPI serves OpenAPI at `/docs` and `/openapi.json`.

## Conventions

- JSON error body:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable explanation",
    "details": [],
    "correlation_id": "uuid"
  }
}
```

- `X-Correlation-ID` is accepted and always returned
- Pagination uses `page`, `page_size`, and `total`
- PATCH and approve require `version` for optimistic concurrency

## Endpoints

### GET /health

Returns `{ status, service, extraction_provider }`.

### GET /ready

Executes `SELECT 1`. Returns 503 if the database is unreachable.

### POST /api/v1/documents

Multipart PDF upload. Rejects non-PDF names, empty files, oversized files, and files that do not start with `%PDF-`.

Optional form fields: `organization_id`, `property_id`, `document_type`, `document_version`, `sample_key`, and `lease_type` (`commercial` or `residential`, default `commercial`). `sample_key` is an explicit fixture identifier. The uploaded filename is never used to select a sample record. Processing resolves specialist flags for the stored lease type.

### POST /api/v1/documents/{document_id}/process

Parse, extract, verify evidence, validate, and index RAG chunks. When multi-agent flags are on, run specialists and the policy engine. A policy `AUTO_APPROVED` result calls the same `apply_approval` helper as human review. Blocking issues keep the lease in `awaiting_review`.

Idempotent for already reviewed or approved documents: returns the existing lease. Failed documents may be retried. In-progress processing returns 409.

### POST /api/v1/demo/samples/{sample_key}/upload

Loads a generated sample by key and stores that key on the document. Optional `lease_type` selects the commercial or residential agent profile. Fixture matching still prefers the verified content hash and rejects a key/hash mismatch. Property A/B/C keys bind the matching demo property so LangGraph can start.

### GET /api/v1/leases?status=

Optional status filter: `awaiting_review` or `approved`.

### PATCH /api/v1/leases/{lease_id}

Corrects field values, increments `version`, writes an audit event, and revalidates.

### POST /api/v1/leases/{lease_id}/approve

Requires no unresolved blocking issues. Calls `apply_approval` with `approval_source=HUMAN_REVIEW`, then commits `approved_by`, `approval_source`, and the audit event in the same transaction.

### GET /api/v1/leases/{lease_id}/export

409 if the lease is not approved.

Additive dashboard helpers: `GET /api/v1/stats`, `GET /api/v1/documents`, and demo sample upload. They do not replace the required review APIs.

### POST /api/v1/rag/search and /api/v1/rag/ask

Require `organization_id` and `property_ids`. The `X-Organization-ID` header must match. Answers include citations or `insufficient_evidence`.

### GET /api/v1/flags/effective

Read-only resolved flags. Optional `lease_type` is `commercial` or `residential`. Property and lease-type settings cannot loosen an organization restriction.

### GET /api/v1/flags/lease-types and POST /api/v1/flags/lease-types/{lease_type}

Manage specialist-agent enablement for commercial versus residential leases. Only agent flags can be written. Disabling a required agent skips that specialist and blocks auto-approval. Approval still goes through `apply_approval`.

### GET /api/v1/leases/{lease_id}/workflow

Latest supervisor run, specialist statuses, MCP tool calls, and policy evaluations.

### POST /api/v1/policy/evaluate

Dry-run of the deterministic policy engine. It does not write approved status.
