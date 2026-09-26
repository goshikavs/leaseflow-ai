# Architecture decisions

ADRs 001–006 record the original take-home decisions. Later ADRs add RAG, MCP, multi-agent behavior, a single approval write-path, and lease-type agent settings on top of that slice. They do not rewrite the earlier choices.

## ADR 001: Modular monolith versus microservices

**Context.** The assignment is a short take-home. The business flow is one document, one extraction, one lease, one approval.

**Decision.** Ship a modular monolith with clear packages (`api`, `extraction`, `workflows`, `integrations`) inside one FastAPI app.

**Alternatives.** Separate upload, extraction, and export services with an async bus.

**Trade-offs.** A monolith is easier to run, test, and explain. It will not scale extractors independently.

**Consequences.** Interviewers can run one backend. A later extraction worker can be split out without changing the data contract.

## ADR 002: SQLite versus PostgreSQL

**Context.** The demo must run without an external database.

**Decision.** Use SQLite locally with SQLAlchemy types and Alembic migrations that stay PostgreSQL-compatible (UUID strings, `Numeric`, timezone-aware datetimes, explicit `Date`).

**Alternatives.** Require Postgres in Docker from day one.

**Trade-offs.** SQLite removes an ops dependency and weakens concurrent write behavior.

**Consequences.** Production should switch `DATABASE_URL` to PostgreSQL and keep the same models. See the roadmap.

## ADR 003: Structured extraction versus full RAG

**Context.** The required output is a closed set of lease fields plus evidence, not portfolio Q&A.

**Decision.** Use structured extraction into a Pydantic schema. Persist evidence. Do not add a vector index.

**Alternatives.** Chunk the lease, embed it, and answer free-form questions.

**Trade-offs.** Structured extraction is testable and cheaper. It cannot answer "what happens if the tenant assigns the lease?"

**Consequences.** RAG remains a future portfolio feature after the system of record exists.

## ADR 004: Deterministic workflow versus LangGraph

**Context.** The workflow is linear with one human loop: extract → verify → validate → correct → approve → export.

**Decision.** Implement the workflow as Python functions and SQLAlchemy transactions. Do not adopt LangGraph.

**Alternatives.** LangGraph with checkpointing.

**Trade-offs.** LangGraph would help if we had long-running multi-agent branching and durable graph state. Here it would add a framework without changing the product.

**Consequences.** Failure states are ordinary database statuses. Retry is an HTTP call, not a graph resume.

## ADR 005: Human approval before export

**Context.** LLM output can omit fields or attach unsupported passages. Downstream rent and date errors are costly.

**Decision.** Export is allowed only for `approved` leases. Approval is a human action. Blocking issues cannot be waived by the model.

**Alternatives.** Auto-export high-confidence extractions.

**Trade-offs.** Reviewer time is required. Operational risk is lower.

**Consequences.** The audit log is the source of approval evidence.

## ADR 006: Versioned downstream integration contract

**Context.** Property-management and financial systems want stable payloads, not raw model JSON.

**Decision.** Export `schema_version: "1.0"` from stored lease fields. Keep extraction output in `extractions.structured_output`.

**Alternatives.** Send the model response to each consumer.

**Trade-offs.** Consumers must map the contract. Extraction changes do not break those mappings as quickly.

**Consequences.** A future queue publisher can emit the same JSON without touching PDF parsing.

## ADR 007: RAG for lease evidence

**Context.** Structured extraction answers a closed field set. Reviewers also ask section-level questions across long leases and amendments.

**Decision.** Chunk parsed pages (~800 tokens, 120 overlap), embed with a local hashing provider, and retrieve with cosine similarity plus organization/property filters.

**Why.** RAG keeps answers tied to stored passages and page numbers. It does not replace the lease system of record.

**Alternatives.** Keyword search only, or paid embedding APIs.

## ADR 008: MCP for departmental context

**Context.** Property, finance, legal, and leasing data is not in the PDF.

**Decision.** Expose fictional team records through official MCP tool servers and an allowlisted application client. Authorization happens in the application before any tool call.

**Why.** MCP is an explicit tool protocol. Ordinary REST wrapped in comments would not be MCP.

## ADR 009: Specialist agents and LangGraph

**Context.** Independent team lookups can run as separate logical agents, then a risk and recommendation step must always run before policy.

**Decision.** Use LangGraph for explicit supervisor routing. Specialist agents do not write approval status. The graph ends at the deterministic policy engine.

**Why.** Separate agents keep tool allowlists small. LangGraph makes the mandatory path visible instead of asking an LLM to improvise approval.

## ADR 010: Deterministic approval remains authoritative

**Context.** Auto-approval is tempting for small internal abstractions and dangerous for large or contested leases.

**Decision.** Keep `ApprovalPolicyEngine` outside the LLM. Auto-approval is allowed only for Prosper Retail Center when every fail-closed condition passes. Dallas is always manual. Logistics escalates on conflict or missing context. Auto-approval never signs a lease or moves funds.

**Why.** Small, complete, low-rent records can skip a reviewer queue. Material office and industrial exceptions cannot.

## ADR 011: One approval write-path

**Context.** Policy-controlled auto-approval was added after the original human-review slice. Writing `lease.status` inside document processing would have created a second approval workflow next to `approve_lease`.

**Decision.** Human review and policy auto-approval both call `apply_approval` in `app/services/approval.py`. The helper re-runs business validation, refuses blocking issues, sets `approval_source` (`HUMAN_REVIEW` or `AUTO_APPROVED`), and writes the `lease_approved` audit event. Agents and RAG stay read-side context.

**Why.** Extraction output, evidence, validation, approval, audit, and export stay on the original tables and services.

**Consequences.** A policy `AUTO_APPROVED` decision that still has blocking issues remains `awaiting_review`. Export is unchanged: only an approved lease can be exported.

## ADR 012: Lease-type scoped specialist enablement

**Context.** Commercial and residential leases need different specialist sets. Property-level flags could express “Dallas is always manual,” but they could not express “skip leasing and run insurance for every residential lease.” Letting a property turn specialists back on would also loosen organization policy.

**Decision.** Persist `documents.lease_type` (`commercial` or `residential`, default `commercial`). Resolve flags as global → organization → lease type → property. Property rows may only tighten approval and never override `AGENT_TOGGLE_KEYS`. Reviewers manage specialist toggles on `/settings` through `POST /api/v1/flags/lease-types/{lease_type}`. Only catalog agent flags can be written there. Optional agents (insurance, recommendation) may be enabled per lease type even when the global default is off. Disabling a required agent skips that specialist and fail-closes auto-approval.

**Why.** Operators can see and change which agents run for each lease category without a competing approval workflow. The backend remains authoritative.

**Consequences.** The LangGraph supervisor reads the document’s lease type. Upload and demo-sample APIs accept `lease_type`. Residential defaults turn leasing off, insurance on, and auto-approval off. Unassigned original samples still skip the entire graph so the original review slice stays visible.

