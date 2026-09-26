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

Missing or incorrect commencement dates, expirations, or rent figures create operational and financial risk. The system keeps the model output separate from the authoritative business record and requires a human approval before export.

## Implemented scope

- PDF upload with type, size, and `%PDF-` validation
- Text extraction with PyMuPDF
- Isolated extraction provider: deterministic fixture adapter (default) or OpenAI-compatible LLM adapter
- Evidence verification against parsed page text
- Deterministic business-rule validation
- Human review, correction, optimistic concurrency, approval, and audit history
- Versioned approved-lease JSON export
- Next.js review UI backed by the FastAPI
- Pytest, Vitest, Playwright smoke tests, GitHub Actions CI, Docker Compose

The original vertical slice is unchanged. This branch adds scoped RAG, a vector store, official MCP team servers, a LangGraph supervisor, org/property feature flags, and a deterministic internal approval policy. Interview notes stay outside Git.

## Architecture overview

```
Browser (Next.js) -> FastAPI
                      |-> SQLite locally / PostgreSQL+pgvector in Compose
                      |-> PDF storage and document chunks
                      |-> Fixture or OpenAI-compatible extractor
                      |-> LangGraph supervisor + specialist agents
                      |-> Allowlisted MCP team servers
                      |-> Deterministic policy engine + audit
```

See [docs/architecture.md](docs/architecture.md), [docs/multi-agent.md](docs/multi-agent.md), and [docs/architecture-decisions.md](docs/architecture-decisions.md).

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

Auto-approval, when it occurs, is an internal lease-abstraction decision only. It never signs a contract or commits funds.

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

### Sample demo flow

1. Open http://localhost:3000/upload
2. Choose **Complete valid lease**
3. Confirm extracted fields and evidence
4. Approve the lease
5. Open the approved export and inspect `schema_version: "1.0"`
6. Repeat with **Missing fields lease** to show blocking issues and corrections

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
- Fixture extraction is deterministic and only matches known sample hashes or filenames.
- Docker was not available in the original Windows implementation environment; Compose files are provided and validated in CI.

## Next steps

See [docs/future-roadmap.md](docs/future-roadmap.md) and [docs/multi-agent.md](docs/multi-agent.md).
