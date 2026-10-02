# LeaseFlow AI

AI-assisted commercial and residential lease intelligence.

LeaseFlow AI is a working vertical slice: upload a fictional commercial or residential lease PDF, extract structured fields, keep the evidence, validate business rules, let a reviewer correct and approve the record, then export a versioned JSON contract. Lease type (`commercial` or `residential`) selects the specialist-agent profile; it does not change the extraction or approval write-path.

This application does **not** provide legal advice and does not claim that extracted lease data is legally correct.

## Problem

Commercial and residential lease documents contain dates, rent, parties, and notice periods that operations and finance teams must move into downstream systems. Manual transcription is slow and error-prone. The useful product is not "an LLM that reads a lease." It is a controlled workflow that turns an unstructured PDF into a reviewable, auditable, exportable record, with specialist agents enabled per lease type.

## Intended users

- Lease administration and CRE operations reviewers
- Integration engineers who need a stable downstream contract

## Why this problem matters

Missing or incorrect commencement dates, expirations, or rent figures create operational and financial risk. The system keeps model output, evidence, and business validation separate from the approved lease record. Export requires an approved lease. Approval is written only through `apply_approval`, whether the actor is a human reviewer or the deterministic policy engine.

Auto-approval is an internal lease-abstraction decision only. It never signs a contract, moves funds, or replaces a human legal or finance sign-off.

## Implemented scope

- PDF upload with type, size, and `%PDF-` validation
- Text extraction with PyMuPDF
- Isolated extraction provider: deterministic fixture adapter (default) or OpenAI-compatible LLM adapter
- Evidence verification against parsed page text
- Deterministic business-rule validation
- Human review, correction, optimistic concurrency, and a single approval write-path with audit history
- Versioned approved-lease JSON export
- Next.js review UI backed by FastAPI
- Scoped RAG, allowlisted MCP team tools, and a LangGraph supervisor that feed the same extraction/review/approval services
- Agent settings UI to enable or disable specialists per lease type (`commercial` or `residential`)
- Pytest, Vitest, Playwright smoke tests, GitHub Actions CI, Docker Compose

The original vertical slice is unchanged: extraction output, evidence, validation, approval, audit, and export remain separate. Agents do not introduce a second approval workflow.

## Architecture overview

```
Browser (Next.js) -> FastAPI
                      |-> SQLite locally / PostgreSQL in Compose
                      |-> PDF storage and document_chunks
                      |-> Fixture or OpenAI-compatible extractor
                      |-> Feature flags (global / org / lease type / property)
                      |-> LangGraph supervisor + specialist agents
                      |-> In-process FastMCP team tools
                      |-> Deterministic policy engine + apply_approval + audit
```

See [docs/architecture.md](docs/architecture.md), [docs/reviewer-verification.md](docs/reviewer-verification.md), [docs/multi-agent.md](docs/multi-agent.md), and [docs/architecture-decisions.md](docs/architecture-decisions.md). How Cursor was used to build it: [docs/ai-assisted-development.md](docs/ai-assisted-development.md) and the project skill in [.cursor/skills/leaseflow-development/SKILL.md](.cursor/skills/leaseflow-development/SKILL.md).

## Persistence, RAG, and MCP

Local development and Compose do not use the same database. RAG and MCP are not separate application services.

| Piece | Local (`uvicorn` / `npm run dev`) | Docker Compose |
| --- | --- | --- |
| App database | SQLite `backend/data/leaseflow.db` | PostgreSQL 16 (`pgvector/pgvector:pg16`, volume `leaseflow-pg`) |
| Uploads | `backend/data/uploads/` | Volume `leaseflow-data` (`STORAGE_DIR=/data/uploads`) |
| RAG | `document_chunks.embedding` is a JSON float array. Embeddings are local hashed n-grams. Cosine similarity runs in the app. | Same table and JSON embeddings. `docker/postgres/init.sql` enables the `vector` extension; search does **not** use pgvector operators. There is no separate vector database. |
| MCP tools | In-process FastMCP modules in `backend/app/mcp/`. `GET /api/v1/mcp/status` reports `transport: "in-process"`. | Same in-process tools inside the API container. The Compose `mcp` service only loops `python -m app.mcp.servers.healthcheck`. It does not serve HTTP, host tools, or write approvals. |
| Migrations | `alembic upgrade head` (also on API startup) | Backend container runs `alembic upgrade head` before uvicorn |

Catalog records in `backend/app/mcp/catalog.py` are fictional. Tool calls persist in `mcp_tool_calls`.

Local defaults in `backend/app/core/config.py`:

```
DATABASE_URL=sqlite:///./data/leaseflow.db
storage_dir=./data/uploads
```

Reset local SQLite by deleting `backend/data/` and rerunning migrations. Reset Compose with `docker compose down -v`, then `docker compose up --build`. Those resets are not interchangeable.

## Technology stack

- Frontend: Next.js App Router, React, TypeScript, Tailwind CSS
- Backend: Python, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PyMuPDF
- Persistence: SQLite locally; PostgreSQL in Compose, with SQLAlchemy types kept compatible
- Tests: Pytest, Vitest, React Testing Library, Playwright
- Packaging: Docker Compose and GitHub Actions

## Local setup

Requirements: Python 3.12+ (developed against a local 3.14 interpreter with 3.12 CI), Node 22+, npm.

One sequence covers dependencies, synthetic PDFs, schema, optional RAG seed, and both processes.

```powershell
python -m pip install -r backend/requirements-dev.txt
python samples/generate_samples.py
cd backend
python -m alembic upgrade head
python -m app.cli seed
python -m app.cli verify-rag
python -m uvicorn app.main:app --reload --port 8000
```

`generate_samples.py` writes the PDFs and `samples/manifest.json`. Alembic creates or upgrades the schema; API startup also runs `upgrade head`. `seed` is idempotent and processes the Harborpoint property samples so Knowledge has chunks. `verify-rag` prints the actual document, chunk, and vector counts plus a sample similarity hit. Do not assume those counts until the command has run.

Seed is optional for the Upload sample buttons. Those buttons call `POST /api/v1/demo/samples/{key}/upload` and process one document at a time.

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

- Frontend: http://localhost:3000
- Agent settings: http://localhost:3000/settings
- Knowledge: http://localhost:3000/knowledge
- Backend: http://localhost:8000
- OpenAPI: http://localhost:8000/docs

### Fixture versus live LLM

Default is fixture mode. No API key is required.

```
EXTRACTION_PROVIDER=fixture
```

To use an OpenAI-compatible provider:

```
EXTRACTION_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-key
LLM_MODEL=gpt-4o-mini
```

Fixture mode is labeled in the UI and API. It demonstrates the workflow, not live LLM accuracy.

### Reviewer verification: two flows

Use the Upload sample buttons. They load generated PDFs from `samples/`. The UI labels **Property A/B/C** map to `prosper_retail_lease.pdf`, `dallas_plaza_lease.pdf`, and `logistics_park_lease.pdf`.

Full click-by-click checklist: [docs/reviewer-verification.md](docs/reviewer-verification.md).

**Flow 1 — Human review.** Property stays `prop-unassigned`. LangGraph does not start.

1. http://localhost:3000/upload → **Complete valid lease** → evidence → **Approve** → export `schema_version: "1.0"`
2. **Missing fields lease** → Approve disabled → correct fields → audit event → approve
3. **Conflicting dates lease** → date-range validator blocks approval

**Flow 2 — Agentic.** Specialists, in-process MCP tools, and policy run because the sample binds a Harborpoint property.

1. http://localhost:3000/settings → confirm commercial vs residential agent toggles
2. Upload, lease type **Commercial** → **Property A: Prosper Retail Center** → specialists SUCCESS, policy can `AUTO_APPROVED` through `apply_approval`
3. **Property B: Dallas Corporate Plaza** → specialists run, `MANUAL_REVIEW_REQUIRED`
4. **Property C** then **Property C amendment** → policy `ESCALATED` (logistics or amendment conflict); not auto-approved
5. Lease type **Residential** → **Property A** → leasing SKIPPED, insurance SUCCESS, auto-approval off

A file-picker upload of a catalog PDF matches the live sample bytes or `manifest.json` hash and binds the same property. An unknown PDF stays `prop-unassigned`, so specialists do not run. The uploaded filename is never a fixture selector.

## Multi-agent implementation

LangGraph runs after extraction, evidence, validation, and RAG indexing. The supervisor starts specialists, then risk, then an advisory recommendation, then the deterministic policy engine. Policy may request `AUTO_APPROVED`; only `apply_approval` writes lease status.

| Agent | Default commercial | Default residential | Role |
| --- | --- | --- | --- |
| Document, Lease RAG, Property, Finance, Legal, Risk | On | On | Required specialists |
| Leasing | On | Off | Negotiation and approved rent |
| Insurance | Off | On | Optional compliance specialist |
| Recommendation | On | On | Advisory only |

Flag precedence is global → organization → lease type → property. A lower scope cannot loosen a disabled required agent or auto-approval. Property rows do not override specialist-agent toggles; those are managed per lease type on **Agent settings**. Disabling a required agent skips that specialist and blocks auto-approval.

Details: [docs/multi-agent.md](docs/multi-agent.md).

## API endpoints

Routes below match the FastAPI routers in `backend/app/api/`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Application status |
| GET | `/ready` | Database readiness |
| GET | `/api/v1/stats` | Dashboard counts |
| GET | `/api/v1/documents` | Paginated documents |
| GET | `/api/v1/demo/samples` | Synthetic sample catalog |
| POST | `/api/v1/documents` | Upload PDF |
| POST | `/api/v1/documents/{id}/process` | Parse, extract, validate, index RAG |
| GET | `/api/v1/documents/{id}` | Document status |
| GET | `/api/v1/leases` | Paginated leases |
| GET | `/api/v1/leases/{id}` | Review payload |
| PATCH | `/api/v1/leases/{id}` | Correct fields |
| POST | `/api/v1/leases/{id}/approve` | Human approval via `apply_approval` |
| GET | `/api/v1/leases/{id}/export` | Versioned JSON (approved only) |
| GET | `/api/v1/leases/{id}/audit` | Change history |
| POST | `/api/v1/rag/search` | Scoped vector search |
| POST | `/api/v1/rag/ask` | Grounded question answering |
| GET | `/api/v1/flags/effective` | Read-only effective flags |
| GET | `/api/v1/flags/lease-types` | Agent toggles by lease type |
| POST | `/api/v1/flags/lease-types/{type}` | Update commercial or residential agents |
| GET | `/api/v1/leases/{id}/workflow` | Agent and policy execution |
| POST | `/api/v1/policy/evaluate` | Dry-run policy evaluation (does not approve) |
| GET | `/api/v1/mcp/status` | In-process MCP discovery status |
| GET | `/api/v1/leases/{id}/audit-timeline` | Workflow audit timeline |
| POST | `/api/v1/demo/samples/{key}/upload` | Load a synthetic sample |

RAG search/ask require `organization_id` and `property_ids`. A mismatched `X-Organization-ID` is 403. That header check is demo scoping, not production authentication.

Narrative notes: [docs/api.md](docs/api.md).

## Test commands

```powershell
cd backend
python -m ruff check .
python -m pytest

cd ../frontend
npm run lint
npm run typecheck
npm test
npm run build
npm run e2e
```

Report only results from a run in this environment. CI also validates `docker compose config`.

## Docker Compose

```powershell
docker compose up --build
```

Frontend remains http://localhost:3000 and the API remains http://localhost:8000. Compose starts PostgreSQL, the API (in-process MCP tools), a catalog health loop, and the UI.

If Docker is not installed locally, use the Python/Node setup. CI still validates `docker compose config`.

## Known limitations

- Single-user demo. There is no production authentication, authorization, SSO, RBAC, or tenant isolation. The actor is the configured `DEMO_ACTOR` (`demo-reviewer`).
- Restricted CORS and the RAG `X-Organization-ID` check are demo boundaries, not an identity system.
- Auto-approval never signs a lease, releases funds, or creates a legal obligation. It only writes the internal lease row through `apply_approval`.
- SQLite is the local default and is not for multi-writer production traffic. Compose PostgreSQL still stores embeddings as JSON; pgvector is enabled, not queried.
- MCP tool calls run in-process. The Compose `mcp` container is a healthcheck, not a networked MCP host.
- Processing is synchronous in the request. That is acceptable for a short PDF demo and would become a queue worker at scale.
- Fixture extraction is deterministic and only matches a verified content hash or an explicit `sample_key`. The hash can come from `samples/manifest.json` or from the live bytes of a catalog PDF. An uploaded PDF named like a sample is not enough.

## Next steps

See [docs/future-roadmap.md](docs/future-roadmap.md) and [docs/multi-agent.md](docs/multi-agent.md).
