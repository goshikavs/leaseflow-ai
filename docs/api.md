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

### POST /api/v1/documents/{document_id}/process

Idempotent for already reviewed or approved documents: returns the existing lease. Failed documents may be retried. In-progress processing returns 409.

### GET /api/v1/leases?status=

Optional status filter: `awaiting_review` or `approved`.

### PATCH /api/v1/leases/{lease_id}

Corrects field values, increments `version`, writes an audit event, and revalidates.

### POST /api/v1/leases/{lease_id}/approve

Requires no unresolved blocking issues. Records `approved_by` and an audit event in the same transaction.

### GET /api/v1/leases/{lease_id}/export

409 if the lease is not approved.

Additive dashboard helpers: `GET /api/v1/stats`, `GET /api/v1/documents`, and demo sample upload. They do not replace the required review APIs.

### POST /api/v1/rag/search and /api/v1/rag/ask

Require `organization_id` and `property_ids`. The `X-Organization-ID` header must match. Answers include citations or `insufficient_evidence`.

### GET /api/v1/flags/effective

Read-only resolved flags. Property settings cannot loosen an organization restriction.

### GET /api/v1/leases/{lease_id}/workflow

Latest supervisor run, specialist statuses, MCP tool calls, and policy evaluations.

### POST /api/v1/policy/evaluate

Dry-run of the deterministic policy engine. It does not write approved status.
