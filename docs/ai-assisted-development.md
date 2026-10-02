# AI-assisted development

LeaseFlow AI was built with Cursor as a pair programmer. Cursor generated and refactored code and found problems; architecture decisions, trust boundaries, and acceptance were decided and reviewed by hand. This page lists the tools used, the prompting approach, and the guardrails that kept generated code reviewable.

## Tools

| Tool | How it was used |
|------|-----------------|
| Cursor Agent (chat) | Multi-file features such as the extraction pipeline, RAG layer, MCP servers, and LangGraph workflow, built one vertical slice at a time |
| Codebase search and `@` file context | Pointing the agent at specific modules (`@backend/app/workflows/processing.py`, `@docs/architecture.md`) so changes followed existing patterns |
| Inline edit | Small, local refactors, type fixes, and test additions |
| Integrated terminal via the agent | Running `pytest`, `ruff`, `npm run lint`, `npm run typecheck`, `npm test`, and Playwright, then iterating on failures |
| Backend skill | `.cursor/skills/leaseflow-backend/SKILL.md` records the trust-model invariants, backend architecture map, change rules, and pytest/ruff verification, and loads for work under `backend/` |
| Frontend skill | `.cursor/skills/leaseflow-frontend/SKILL.md` records UI rules (API client only, backend decides approval, evidence beside every field, accessibility), test conventions, and lint/typecheck/Vitest/Playwright verification, and loads for work under `frontend/` |
| Cloud Agents | Longer background tasks on a branch, opened as draft pull requests for review |
| GitHub Actions | Final gate: backend lint and tests, frontend lint, typecheck, tests, and build, Compose validation, and end-to-end tests |

## Workflow

1. **Design first.** Write or update the relevant section of `docs/architecture.md` or an ADR in `docs/architecture-decisions.md`, then ask the agent to implement against it.
2. **Vertical slices.** Each prompt covered one end-to-end capability (upload → extract → review → export, then RAG, then MCP and agents, then policy) instead of one layer at a time.
3. **Tests in the same change.** Every prompt asked for tests alongside the code, and the agent ran them before the change was accepted.
4. **Review every diff.** Generated code was read line by line, with extra attention to approval, policy, flag precedence, and organization scoping.
5. **Small commits.** One logical change per commit, matching the history on `main`.

## Prompt patterns

The prompts below are representative of the ones used for each phase. Each states the goal, the constraints, the files to follow, and how to verify.

### Initial slice

> Build a FastAPI backend and Next.js review console for lease abstraction. Upload a PDF, validate it is a real PDF under the size limit, store it with a SHA-256 hash, parse pages with PyMuPDF, extract tenant, property, dates, rent, deposit, and renewal fields, and show each field with its evidence passage for human review. Raw extraction output must never be written to the lease directly; only fields whose evidence passage is found in the page text may be. Add pytest and Vitest coverage, and keep it runnable without an LLM key.

### Deterministic extraction

> Add an `ExtractionProvider` interface with two implementations: a fixture provider that returns pre-written results from `samples/manifest.json`, and an OpenAI-compatible provider using a strict JSON schema at temperature 0 with timeouts, retries, and a response size limit. Fixture selection must use the file's content hash or an explicit `sample_key`, never the filename. Unknown PDFs return every field as missing.

### RAG, MCP, and agents

> Following `@docs/architecture.md`, add document chunking and embeddings behind an `EmbeddingProvider`, organization-scoped vector search, and amendment conflict detection. Expose lease, property, and compliance data through MCP servers with a tool allowlist. Build a LangGraph workflow where specialist agents call tools only through the MCP client, then a risk node, recommendation node, and policy node. Agents must fail closed.

### Policy-controlled approval

> Route policy auto-approval through the existing `apply_approval` service so human and automated approvals share one write path and audit event, with `approval_source` recorded. Add tests for each policy outcome and for flag precedence where a property cannot loosen lease-type settings.

### Debugging and CI

> CI fails on `npm ci` in Linux with platform-specific lightningcss packages in the lockfile. Find the cause and fix it without changing application behavior.

> The file picker upload of a sample PDF gets no fixture fields when the manifest hash is stale. Match against the live sample file bytes as a fallback, and add a test.

### Review prompts

> Review `@backend/app/workflows/processing.py` and `@backend/app/policy/engine.py` for concurrency issues, transaction boundaries, and any path where a lease could be approved without passing validation. List findings with file and line; do not change code yet.

> Compare the scenario outcomes documented in `README.md` and `docs/multi-agent.md` with what the tests assert. Report any mismatch.

## Guardrails on generated code

- **Skills are split by layer.** Backend and frontend work load different skills, so each session gets only the rules for the code it touches. The shared boundary is the API contract: a backend response change must update `frontend/lib/types.ts` in the same change.
- **Invariants live in the repo.** The backend skill lists the rules that generated changes must keep: three trust layers, evidence before data, one approval path, fail closed, tighten-only flags, content-hash fixtures, organization isolation, approved-only export. The frontend skill adds that the UI never computes approval eligibility itself.
- **Determinism by default.** `EXTRACTION_PROVIDER=fixture` keeps tests and CI free of network calls, secrets, and model variance.
- **No secrets in prompts or code.** Keys come from `.env` (see `.env.example`), and the agent never needed real credentials.
- **The LLM is limited to extraction.** Agents, policy, RAG answers, approval, and export are deterministic code, so AI-generated suggestions cannot approve a lease.
- **Human ownership.** Cursor proposed changes; each one was reviewed, tested locally, and passed CI before merge.

## What worked and what needed correction

- Worked well: scaffolding, Pydantic and SQLAlchemy models, migrations, test cases for edge conditions, and diagnosing CI failures from logs.
- Needed close review: transaction and concurrency handling, keeping docs aligned with actual policy outcomes, and making sure fixture selection could not fall back to filenames.
- Kept by hand: the trust model, approval rules, flag precedence, and the decision to keep the LLM out of approval.
