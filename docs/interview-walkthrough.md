# Interview walkthrough

## Why this business problem

Newmark's domain is commercial real estate. A Staff engineer take-home should show product judgment, not a generic chatbot. Lease documents already contain the dates and financial terms that operations teams re-key into other systems. That is a concrete CRE workflow with measurable risk: a wrong expiration or rent figure is worse than a missing chatbot answer.

The selected slice is narrow on purpose: eight fields, evidence, validation, human approval, and a versioned export.

## What research informed the decision

Public lease-administration and lease-accounting material describes abstraction and data capture as operational work. Public LLM documentation and the NIST AI RMF support treating model output as untrusted. No Newmark internal architecture was used or inferred.

## How scope was prioritized

Must work in a short assignment:

1. Upload and parse a PDF
2. Deterministic extraction for demo and tests
3. Evidence check
4. Business rules
5. Review UI
6. Approval + export + audit
7. Automated tests and CI

Explicitly deferred: RAG, Kafka, Kubernetes, SSO, multi-tenant isolation, and live PMS integrations. Those belong on a roadmap after the system of record exists.

## Why these architectural choices

- Modular monolith: one process an interviewer can run
- SQLite: no external database for the demo
- Structured extraction instead of RAG: closed schema, testable evidence
- Python functions instead of LangGraph: the graph would not add durable value here
- Human approval before export: the LLM is not an authority
- Versioned JSON: downstream systems should not consume raw model output

## How to demonstrate the application

1. Start backend and frontend with fixture mode (see README)
2. Upload **Complete valid lease**
3. Show evidence passages and the fixture-mode label
4. Approve and export `schema_version` 1.0
5. Upload **Missing fields lease**
6. Show blocking issues and a disabled Approve button
7. Correct property, landlord, and rent
8. Show the audit event for the correction
9. Optionally show **Conflicting dates lease** and the date-range rule
10. Open `/docs` and `docs/architecture-decisions.md`

Do not present fixture results as live model accuracy.

## What was deliberately excluded

Production authentication, object storage, async workers, vector search, amendment versioning, and client-specific adapters. Excluding them is a scope decision, not an unfinished half-build.

## Production roadmap

See [future-roadmap.md](future-roadmap.md). The first production increments would be identity, PostgreSQL, object storage, and an async processing queue.
