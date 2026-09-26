# LeaseFlow AI

AI-assisted commercial lease intelligence for a Staff Software Engineer take-home assignment.

LeaseFlow AI is a working vertical slice: upload a fictional commercial lease PDF, extract structured fields, keep the evidence, validate business rules, let a human correct and approve the record, then export a versioned JSON contract.

This application does **not** provide legal advice and does not claim that extracted lease data is legally correct.

## Problem

Commercial lease documents contain dates, rent, parties, and notice periods that operations and finance teams must move into downstream systems. Manual transcription is slow and error-prone. The useful product is not "an LLM that reads a lease." It is a controlled workflow that turns an unstructured PDF into a reviewable, auditable, exportable record.

## Intended users

- Lease administration and CRE operations reviewers
- Integration engineers who need a stable downstream contract
- Interviewers evaluating architectural judgment on a short assignment

## Why this problem matters

Missing or incorrect commencement dates, expirations, or rent figures create operational and financial risk. The system keeps model output, evidence, and business validation separate from the approved lease record. Export requires an approved lease. Approval is written only through `apply_approval`, whether the actor is a human reviewer or the deterministic policy engine.

## Implemented scope

- PDF upload with type, size, and `%PDF-` validation
- Text extraction with PyMuPDF
- Isolated extraction provider: deterministic fixture adapter (default) or OpenAI-compatible LLM adapter
- Evidence verification against parsed page text
- Deterministic business-rule validation
- Human review, correction, optimistic concurrency, and a single approval write-path with audit history
- Versioned approved-lease JSON export
- Next.js review UI backed by the FastAPI
- Scoped RAG, official MCP team servers, and a LangGraph supervisor that feed the same extraction/review/approval services
- Agent settings UI to enable or disable specialists per lease type (`commercial` or `residential`)
- Pytest, Vitest, Playwright smoke tests, GitHub Actions CI, Docker Compose

The original vertical slice is unchanged: extraction output, evidence, validation, approval, audit, and export remain separate. Agents do not introduce a second approval workflow. Interview notes stay outside Git.

## Architecture overview

```
Browser (Next.js) -> FastAPI
                      |-> SQLite locally / PostgreSQL+pgvector in Compose
                      |-> PDF storage and document chunks
                      |-> Fixture or OpenAI-compatible extractor
                      |-> Feature flags (global / org / lease type / property)
                      |-> LangGraph supervisor + specialist agents
                      |-> Allowlisted MCP team servers
                      |-> Deterministic policy engine + apply_approval + audit
```

See [docs/architecture.md](docs/architecture.md), [docs/reviewer-verification.md](docs/reviewer-verification.md), [docs/multi-agent.md](docs/multi-agent.md), and [docs/architecture-decisions.md](docs/architecture-decisions.md).

## Where RAG, MCP, and data live

They are not separate services in the local demo. All three sit inside the FastAPI process.

| Piece | Code | What a reviewer opens | Where data is stored |
| --- | --- | --- | --- |
| RAG | `backend/app/rag/` (`chunking.py`, `embeddings.py`, `service.py`) | Knowledge page http://localhost:3000/knowledge, `POST /api/v1/rag/search` and `/ask` | `document_chunks` table. Embeddings are a JSON float array in SQLite. Compose uses PostgreSQL + pgvector. |
| MCP | `backend/app/mcp/` (`catalog.py`, `client.py`, `servers/`) | Lease review specialist/tool sections, `GET /api/v1/mcp/status` | Fictional team records in `catalog.py`. Tool calls persist in `mcp_tool_calls`. Compose also runs `python -m app.mcp.servers.healthcheck`. |
| App data | `backend/app/models/`, `backend/app/core/config.py`, `backend/alembic/` | Review, audit, export, Agent settings | Local SQLite `backend/data/leaseflow.db`. Uploaded PDFs in `backend/data/uploads/`. Generated samples in `samples/`. |
| Agents / policy | `backend/app/agents/`, `backend/app/policy/` | Review workflow panel, `/settings` | `workflow_executions`, `agent_executions`, `policy_evaluations`, `feature_flags` |

Local defaults in `backend/app/core/config.py`:

```
DATABASE_URL=sqlite:///./data/leaseflow.db
storage_dir=./data/uploads
```

Reset the demo by deleting `backend/data/` and running `alembic upgrade head`. Docker Compose switches the database to PostgreSQL (`docker-compose.yml`, volume `leaseflow-pg`) and keeps the same models. RAG vectors stay in `document_chunks`; there is no separate vector database.

## Technology stack

- Frontend: Next.js App Router, React, TypeScript, Tailwind CSS
- Backend: Python, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PyMuPDF
- Persistence: SQLite locally, types chosen to stay PostgreSQL-compatible
- Tests: Pytest, Vitest, React Testing Library, Playwright
- Packaging: Docker Compose and GitHub Actions

## Local quick start

Requirements: Python 3.12+ (developed against a local 3.14 interpreter with 3.12 CI), Node 22+, npm.

```powershell
python -m pip install -r backend/requirements-dev.txt
python samples/generate_samples.py
cd backend
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

- Frontend: http://localhost:3000
- Agent settings: http://localhost:3000/settings
- Backend: http://localhost:8000
- OpenAPI: http://localhost:8000/docs

Reset the local demo by deleting `backend/data/` and rerunning `alembic upgrade head`.

### Seed synthetic properties and vectors

```powershell
python samples/generate_samples.py
cd backend
python -m app.cli seed
python -m app.cli verify-rag
```

The seed is idempotent. `verify-rag` prints actual document, chunk, and vector counts plus a sample similarity hit with page references. Do not assume a count until the command has run.

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

Use the Upload sample buttons. They load generated PDFs from `samples/` (run `python samples/generate_samples.py` if those files are missing). The UI labels **Property A/B/C** map to `prosper_retail_lease.pdf`, `dallas_plaza_lease.pdf`, and `logistics_park_lease.pdf`.

Full click-by-click checklist: [docs/reviewer-verification.md](docs/reviewer-verification.md).

**Flow 1 — Human review.** Property stays `prop-unassigned`. LangGraph does not start.

1. http://localhost:3000/upload → **Complete valid lease** → evidence → **Approve** → export `schema_version: "1.0"`
2. **Missing fields lease** → Approve disabled → correct fields → audit event → approve
3. **Conflicting dates lease** → date-range validator blocks approval

**Flow 2 — Agentic.** Specialists, MCP, and policy run because the sample binds a Harborpoint property.

1. http://localhost:3000/settings → confirm commercial vs residential agent toggles
2. Upload, lease type **Commercial** → **Property A: Prosper Retail Center** → specialists SUCCESS, policy can `AUTO_APPROVED` through `apply_approval`
3. **Property B: Dallas Corporate Plaza** → specialists run, `MANUAL_REVIEW_REQUIRED`
4. **Property C** then **Property C amendment** → not auto-approved; amendment conflict escalates or blocks
5. Lease type **Residential** → **Property A** → leasing SKIPPED, insurance SUCCESS, auto-approval off

Do not expect agents on the first three samples, or on a file-picked PDF that does not match a seeded Property A/B/C hash. Auto-approval is an internal lease-abstraction decision only. It never signs a contract or commits funds.

## Multi-agent implementation

LangGraph runs after extraction, evidence, validation, and RAG indexing. The supervisor starts specialists, then risk, then an advisory recommendation, then the deterministic policy engine. Policy may request `AUTO_APPROVED`; only `apply_approval` writes lease status.

| Agent | Default commercial | Default residential | Role |
| --- | --- | --- | --- |
| Document, Lease RAG, Property, Finance, Legal, Risk | On | On | Required specialists |
| Leasing | On | Off | Negotiation and approved rent |
| Insurance | Off | On | Optional compliance specialist |
| Recommendation | On | On | Advisory only |

Flag precedence is global → organization → lease type → property. A lower scope cannot loosen a disabled required agent or auto-approval. Property rows do not override specialist-agent toggles; those are managed per lease type on **Agent settings**. Disabling a required agent skips that specialist and blocks auto-approval.

Auto-approval, when it occurs, is an internal lease-abstraction decision only. It never signs a contract or commits funds.

Details: [docs/multi-agent.md](docs/multi-agent.md).

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Application status |
| GET | `/ready` | Database readiness |
| GET | `/api/v1/stats` | Dashboard counts |
| GET | `/api/v1/documents` | Paginated documents |
| POST | `/api/v1/documents` | Upload PDF |
| POST | `/api/v1/documents/{id}/process` | Parse, extract, validate |
| GET | `/api/v1/documents/{id}` | Document status |
| GET | `/api/v1/leases` | Paginated leases |
| GET | `/api/v1/leases/{id}` | Review payload |
| PATCH | `/api/v1/leases/{id}` | Correct fields |
| POST | `/api/v1/leases/{id}/approve` | Human approval |
| GET | `/api/v1/leases/{id}/export` | Versioned JSON |
| GET | `/api/v1/leases/{id}/audit` | Change history |
| POST | `/api/v1/rag/search` | Scoped vector search |
| POST | `/api/v1/rag/ask` | Grounded question answering |
| GET | `/api/v1/flags/effective` | Read-only effective flags |
| GET | `/api/v1/flags/lease-types` | Agent toggles by lease type |
| POST | `/api/v1/flags/lease-types/{type}` | Update commercial or residential agents |
| GET | `/api/v1/leases/{id}/workflow` | Agent and policy execution |
| POST | `/api/v1/policy/evaluate` | Dry-run policy evaluation |
| GET | `/api/v1/mcp/status` | MCP discovery status |
| GET | `/api/v1/leases/{id}/audit-timeline` | Workflow audit timeline |
| POST | `/api/v1/demo/samples/{key}/upload` | Load a synthetic sample |

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

## Docker Compose

```powershell
docker compose up --build
```

Frontend remains http://localhost:3000 and the API remains http://localhost:8000. Compose starts PostgreSQL with pgvector, the API, an MCP catalog health process, and the UI.

If Docker is not installed locally, use the Python/Node quick start. CI still validates `docker compose config`.

## Known limitations

- Single-user demo model. There is no production authentication, authorization, or tenant isolation.
- SQLite is for the assignment, not multi-writer production traffic.
- Processing is synchronous in the request. That is acceptable for a short PDF demo and would become a queue worker at scale.
- Fixture extraction is deterministic and only matches a verified content hash or an explicit `sample_key`. An uploaded PDF named like a sample is not enough.
- Docker was not available in the original Windows implementation environment; Compose files are provided and validated in CI.

## Next steps

See [docs/future-roadmap.md](docs/future-roadmap.md) and [docs/multi-agent.md](docs/multi-agent.md).
