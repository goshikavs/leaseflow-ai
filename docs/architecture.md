# Architecture

LeaseFlow AI is a modular monolith: one FastAPI process, one Next.js UI, and one relational database.

## Component diagram

```mermaid
flowchart LR
  reviewer[Reviewer browser]
  ui[Next.js App Router]
  api[FastAPI]
  db[(SQLite / PostgreSQL)]
  rag[Document chunks]
  mcp[MCP team servers]
  graph[LangGraph supervisor]
  files[PDF storage]
  extract[Extraction provider]
  reviewer --> ui --> api
  api --> db
  api --> files
  api --> extract
  api --> rag
  api --> graph --> mcp
  graph --> db
```

The backend owns documents, extractions, leases, evidence, validation issues, audit events, and export events. The frontend is a review console. It does not keep an authoritative copy of lease data.

## Sequence diagram

```mermaid
sequenceDiagram
  participant R as Reviewer
  participant UI as Next.js
  participant API as FastAPI
  participant P as PDF parser
  participant X as Extractor
  participant RAG as RAG index
  participant G as LangGraph
  participant A as apply_approval
  participant DB as SQLite
  R->>UI: Upload PDF or choose sample
  UI->>API: POST /api/v1/documents
  API->>DB: Store document metadata
  UI->>API: POST /api/v1/documents/{id}/process
  API->>P: Parse page text
  API->>X: Structured extraction
  API->>API: Verify evidence passages
  API->>API: Validate business rules
  API->>DB: Persist extraction, lease, evidence, issues
  API->>RAG: Chunk and embed parsed text
  API->>G: Specialists, risk, recommendation, policy
  alt Policy AUTO_APPROVED
    G->>A: Same approval service
    A->>DB: Status, audit, approval_source
  else Manual review
    R->>UI: Correct and approve
    UI->>API: PATCH then POST approve
    API->>A: Same approval service
    A->>DB: Status, audit, approval_source
  end
  R->>UI: Export
  UI->>API: GET export
  API-->>UI: schema_version 1.0 JSON
```

## Data model

Core tables match the assignment:

- `documents`: upload metadata, content hash, optional `sample_key`, processing status
- `leases`: authoritative business record, optimistic `version`, `approval_source`
- `extractions`: provider output kept separate from the lease
- `field_evidence`: page, passage, extracted value, evidence status
- `validation_issues`: blocking / warning / information, with `resolved_at`
- `audit_events`: actor, event type, change details
- `export_events`: schema version and payload hash
- `document_chunks`: RAG passages with organization/property filters (not a second system of record)

Monetary amounts use `Numeric(14, 2)`. Dates use SQL `Date`. IDs are UUID strings for SQLite/PostgreSQL portability.

## Extraction and approval flow

Persisted document states: `uploaded` → `processing` → `awaiting_review` → `approved`, or `failed`.

Lease states: `draft` / `awaiting_review` → `approved`.

The workflow is ordinary Python in `app/workflows/processing.py`, then `app/services/approval.py`:

1. Parse PDF text
2. Call the configured provider (fixture match is hash or explicit `sample_key` only)
3. Verify each evidence passage against page text
4. Copy only evidence-backed values into the lease
5. Run deterministic validators
6. Index chunks for RAG and, when flagged, run the LangGraph specialists
7. Policy may request auto-approval; it cannot write `lease.status` itself
8. `apply_approval` revalidates, writes approved status and audit, or leaves the lease in review
9. Humans correct and approve through the same helper
10. Export the versioned contract only after approval

Extraction output stays in `extractions` / `field_evidence`. Agents, RAG, and MCP enrich context. They do not replace the lease record or create a second approval path.

The LLM never approves, rejects, or exports.

## Security and reliability boundaries

Implemented now:

- Upload size limit, PDF header check, randomized stored filenames
- Restricted CORS from configuration
- Secrets from environment variables
- Parameterized SQLAlchemy access
- Bounded LLM timeout, retries, and response size
- Correlation IDs on responses
- No stack traces in API bodies
- Document content is not written to application logs

Not implemented, and not claimed:

- Authentication, SSO, RBAC, or tenant isolation
- Object storage virus scanning
- Cross-region replication or HA

This is a labeled single-user demo.
