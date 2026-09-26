# Prompt 01: project design

## Actual source

The initiating prompt was the take-home specification provided in this chat on 2026-09-25: design, implement, test, document, and push LeaseFlow AI for a Newmark Staff Software Engineer assignment.

## Design decisions recorded from that prompt

- Narrow vertical slice over unfinished platform sprawl
- CRE lease extraction with human approval, not a legal-advice product
- Modular monolith, SQLite, fixture + OpenAI-compatible adapters
- No Kafka, Kubernetes, Redis, or vector database in v1
- LangGraph rejected unless checkpointing added concrete value; it did not
- Fictional companies and documents only

## Rejected AI-leaning expansions

- Multi-service extract/review/export split
- RAG over the sample PDFs
- Decorative dashboard charts
- Implicit auto-approval of high-confidence fields
