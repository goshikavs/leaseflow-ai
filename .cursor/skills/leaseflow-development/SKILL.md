---
name: leaseflow-development
description: Conventions, invariants, and verification steps for changing LeaseFlow AI (FastAPI backend, Next.js review console, RAG, MCP, LangGraph agents, policy-controlled approval). Use when adding features, fixing bugs, or reviewing changes anywhere in this repository.
---

# LeaseFlow AI development

LeaseFlow AI turns lease PDFs into reviewed, approved lease records. Every change must keep the trust model intact: raw model output is never the system of record.

## Architecture map

| Area | Location |
|------|----------|
| Upload and processing pipeline | `backend/app/workflows/processing.py` |
| Extraction providers (fixture, OpenAI-compatible) | `backend/app/extraction/providers/` |
| Evidence verification | `backend/app/extraction/evidence.py` |
| Field mapping and validation | `backend/app/services/mapping.py`, `backend/app/services/validation.py` |
| Approval (single write path) | `backend/app/services/approval.py` |
| Feature flags and policy | `backend/app/policy/flags.py`, `backend/app/policy/engine.py` |
| LangGraph workflow and specialists | `backend/app/agents/graph.py`, `backend/app/agents/specialists.py` |
| MCP client and tool servers | `backend/app/mcp/` |
| RAG chunking, embeddings, search | `backend/app/rag/` |
| Schema migrations | `backend/alembic/versions/` |
| Review console | `frontend/components/`, `frontend/lib/api.ts` |

## Invariants

Do not break these. Add or update a test when touching the code that enforces them.

1. **Three trust layers.** `extractions` stores raw provider output, `field_evidence` stores verification results, and `leases` stores only values whose status is `evidence_found` (`authoritative_value` in `mapping.py`).
2. **Evidence before data.** A provider value without an exact supporting passage in the parsed PDF text must not reach the lease.
3. **One approval path.** Human approval and policy auto-approval both go through `apply_approval`, which re-runs validation, bumps the lease version, and writes a `lease_approved` audit event with `approval_source`.
4. **Fail closed.** Missing flags, failed mandatory agents, blocking validation issues, or unknown properties must lead to manual review or a block, never to auto-approval.
5. **Flags only tighten.** Precedence is defaults, global, organization, lease type, property, then kill switch. A property cannot re-enable agents disabled at the lease-type level.
6. **Fixtures match by content.** The fixture provider selects answers by SHA-256 of the file bytes or an explicit `sample_key`. Never select by filename.
7. **Organization isolation.** RAG search, MCP tool calls, and lease queries are scoped to the caller's organization.
8. **Export is approved-only.** Export schema version `1.0` is produced only for approved leases.

## Making a change

1. Read the relevant module and its tests in `backend/tests/` or `frontend/tests/` before editing.
2. Schema changes need a new Alembic migration. Do not edit an existing migration.
3. New extraction providers implement `ExtractionProvider` and return `LeaseExtractionResult`, so verification applies unchanged.
4. New specialist agents are registered in `SPECIALIST_TOOLS` and `AGENT_REGISTRY`, call tools only through `McpClient`, and must appear in `TOOL_ALLOWLIST`.
5. Policy changes go in `evaluate_policy` with a test per outcome: `AUTO_APPROVED`, `MANUAL_REVIEW_REQUIRED`, `ESCALATED`, `BLOCKED`.
6. Keep docs in `docs/` consistent with behavior. If a scenario outcome changes, update `README.md`, `docs/multi-agent.md`, and `docs/reviewer-verification.md` together.
7. Keep the default `EXTRACTION_PROVIDER=fixture` so tests and CI never need network access or secrets.

## Verification

Run the same checks CI runs (`.github/workflows/ci.yml`):

```bash
cd backend
python -m pip install -r requirements-dev.txt
python ../samples/generate_samples.py
python -m ruff check .
python -m pytest

cd ../frontend
npm ci
npm run lint
npm run typecheck
npm test
npm run build
```

End-to-end, when browsers are available:

```bash
cd frontend
npx playwright install chromium
npm run e2e
```

`samples/generate_samples.py` rewrites the tracked sample PDFs and manifest. Restore them with `git checkout -- samples` unless the change is intentional.

Seed and smoke-test RAG locally:

```bash
cd backend
python -m app.cli seed
python -m app.cli verify-rag
```

## Commit style

One logical change per commit, with a sentence-style message describing the behavior change, for example "Route policy auto-approval through the existing approval service and match fixtures by hash or sample key only."
