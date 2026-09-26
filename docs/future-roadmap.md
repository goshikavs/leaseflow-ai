# Future roadmap

The items below are **not implemented**. They are follow-on capabilities after the working vertical slice.

## Enterprise authentication and authorization

Replace the labeled `demo-reviewer` actor with SSO, role-based review/approve/export permissions, and session management.

## Multi-tenant isolation

Add organization IDs to every table, enforce row-level access, and isolate storage prefixes. The current schema has no tenant boundary.

## PostgreSQL migration

Point `DATABASE_URL` at PostgreSQL, keep Alembic, and add connection pooling. SQLite remains the local assignment default.

## Object storage

Move PDFs from local disk to S3-compatible storage with server-side encryption and lifecycle policies.

## Asynchronous processing and queues

A queue (SQS, Pub/Sub, or Kafka at larger scale) would fit when PDFs are large, LLM latency is high, or extraction must retry independently of HTTP. Kafka is not justified for this demo.

## Observability

Structured logs already include correlation IDs. Production would add metrics, tracing, and an operations dashboard for processing failures and review SLA.

## Real client-system integrations

Publish the 1.0 export contract to a client API or queue. Mapping belongs in an anti-corruption layer, not in the extractor.

## Document amendment processing

Treat amendments as new documents linked to a lease version chain rather than overwriting history.

## RAG-based portfolio questions

After structured records exist, embed approved clause text for retrieval over a portfolio. A vector database belongs here, not in the first extraction path.

## Human evaluation of LLM quality

Build a labeled evaluation set from synthetic and licensed documents. Track field-level precision/recall separately from fixture-mode demos.

## Infrastructure as code and orchestration

Terraform or equivalent for cloud resources. Kubernetes only if many services and teams need independent deploy cadence. Docker Compose is enough for this assignment.
