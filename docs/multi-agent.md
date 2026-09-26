# Multi-agent, RAG, and MCP

LeaseFlow remains a modular monolith. Logical layers live in one FastAPI process.

```
API -> application workflows -> AI (RAG, agents) -> integrations (MCP) -> domain -> infrastructure
```

Code map (same process):

| Concern | Path |
| --- | --- |
| RAG chunk, embed, search | `backend/app/rag/` |
| MCP catalog, client, FastMCP servers | `backend/app/mcp/` |
| LangGraph supervisor and specialists | `backend/app/agents/` |
| Database, uploads, samples | `backend/data/leaseflow.db`, `backend/data/uploads/`, `samples/` |

See the README section **Where RAG, MCP, and data live** and [architecture.md](architecture.md) for storage details.

## Multi-agent graph

```mermaid
flowchart TD
  start[Supervisor initializes state] --> specialists[Document + RAG + team agents]
  specialists --> risk[Risk agent]
  risk --> recommend[Approval recommendation agent]
  recommend --> policy[Deterministic policy engine]
  policy --> persist[apply_approval + audit]
```

The graph starts only after extraction, evidence, validation, and RAG indexing, and only when `ENABLE_MULTI_AGENT` is on and `documents.property_id` is not `prop-unassigned`. Disabled specialists persist as `SKIPPED`. A disabled required agent fail-closes auto-approval.

Independent team agents are registered in `AGENT_REGISTRY` and described in `AGENT_CATALOG` for the settings UI. Adding Insurance Compliance only requires a catalog entry, an optional flag, and a registry row. Other specialists do not change.

| Agent | Flag | Default commercial | Default residential |
| --- | --- | --- | --- |
| document | `ENABLE_DOCUMENT_AGENT` | On | On |
| lease_rag | `ENABLE_LEASE_RAG_AGENT` | On | On |
| property | `ENABLE_PROPERTY_AGENT` | On | On |
| finance | `ENABLE_FINANCE_AGENT` | On | On |
| legal | `ENABLE_LEGAL_AGENT` | On | On |
| leasing | `ENABLE_LEASING_AGENT` | On | Off |
| insurance | `ENABLE_INSURANCE_AGENT` | Off | On |
| risk | `ENABLE_RISK_AGENT` | On | On |
| recommendation | `ENABLE_RECOMMENDATION_AGENT` | On | On |

## RAG ingestion

PDF → page text → section-aware chunks → local embeddings → `document_chunks` → filtered cosine search.

Metadata stored with every chunk: organization, property, lease, document, version, chunk id, heading, page range, source text, content hash, embedding model/version.

Vector queries always filter organization and allowed properties.

## Vector schema

`document_chunks.embedding` is a JSON float array so SQLite tests and PostgreSQL both work. Docker Compose starts `pgvector/pgvector:pg16` and enables the `vector` extension. Similarity is computed in the application against stored vectors, not keyword stubs.

## MCP contracts

Local transport for the demo is in-process invoke plus official FastMCP stdio servers:

| Server | Tools |
| --- | --- |
| property | `get_property_profile`, `get_property_maintenance_status` |
| finance | `get_tenant_financial_status`, `get_property_financial_thresholds` |
| legal | `get_legal_review_status`, `get_approved_clause_templates` |
| leasing | `get_leasing_context`, `get_lease_negotiation_status` |
| insurance | `get_insurance_compliance` (optional) |

MCP responses cannot override application authorization or approval policy.

## Feature-flag precedence

1. Code defaults
2. Global rows
3. Organization rows (ceiling)
4. Lease-type rows (`commercial` or `residential`) for specialist-agent toggles
5. Property rows (may only tighten approval; they do not override specialist-agent flags)
6. Emergency kill switch `AUTO_APPROVAL_KILL_SWITCH`

A property cannot enable auto-approval if the organization or global policy disabled it. Lease-type settings cannot turn on an agent the organization disabled. Reviewers manage specialist toggles at http://localhost:3000/settings. Frontend flags are display-only until saved through `POST /api/v1/flags/lease-types/{lease_type}`.

## Approval policy

Outputs: `AUTO_APPROVED`, `MANUAL_REVIEW_REQUIRED`, `ESCALATED`, `BLOCKED`.

Fail-closed on missing evidence, failed mandatory tools/agents, disabled required agents, stale versions, kill switch, or blocking validation. The recommendation agent is advisory. The policy engine may request `AUTO_APPROVED`. Only `apply_approval` writes lease approval status, using the same validation and audit rules as `POST /api/v1/leases/{id}/approve`.

## How to add an agent or MCP server

1. Add fictional records and allowlisted tools in `app/mcp/catalog.py`.
2. Build a FastMCP module with `build_server("name")`.
3. Register the agent flag and `AGENT_REGISTRY` / `SPECIALIST_TOOLS` / `AGENT_CATALOG` entries.
4. If the agent is optional, keep it out of `MANDATORY_AGENTS` and `TIGHTEN_ENABLE_KEYS` so a lease type can enable it.
5. Seed any lease-type default in `LEASE_TYPE_DEFAULTS`.
6. Add tests for discovery, authorization, lease-type toggles, and policy impact.

Reviewers then enable or disable the new specialist on `/settings` without a code change to the approval path.
