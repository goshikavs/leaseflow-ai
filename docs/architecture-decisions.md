# Architecture decisions

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
