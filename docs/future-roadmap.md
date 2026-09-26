# Future roadmap

The items below are **not implemented**. They are follow-on capabilities after the working vertical slice.

## Enterprise authentication and authorization

Replace the labeled `demo-reviewer` actor with SSO, role-based review/approve/export permissions, and session management.

## Multi-tenant isolation

Documents, leases, chunks, and workflow rows already store `organization_id`. RAG rejects a mismatched `X-Organization-ID`. What is not implemented is production auth, RBAC, or enforced row-level isolation.

## PostgreSQL migration

Docker Compose already runs PostgreSQL with pgvector. The remaining work is production pooling, backups, and ops. SQLite remains the local assignment default.

## Object storage

Move PDFs from local disk to S3-compatible storage with server-side encryption and lifecycle policies.

## Asynchronous processing and queues

A queue (SQS, Pub/Sub, or Kafka at larger scale) would fit when PDFs are large, LLM latency is high, or extraction must retry independently of HTTP. Kafka is not justified for this demo.

## Observability

Structured logs already include correlation IDs. Production would add metrics, tracing, and an operations dashboard for processing failures and review SLA.

## Real client-system integrations

Publish the 1.0 export contract to a client API or queue. Mapping belongs in an anti-corruption layer, not in the extractor.

## Document amendment processing

The demo indexes a Property C amendment and can escalate on detected conflicts. A durable amendment version chain and full lease-history UI are not implemented.

## RAG-based portfolio questions

Scoped RAG over parsed PDF chunks is implemented (`document_chunks`, `/knowledge`). What is not implemented is portfolio-wide search over approved records, a dedicated vector database, or paid embedding APIs.

## Human evaluation of LLM quality

Build a labeled evaluation set from synthetic and licensed documents. Track field-level precision/recall separately from fixture-mode demos.

## Infrastructure as code and orchestration

Terraform or equivalent for cloud resources. Kubernetes only if many services and teams need independent deploy cadence. Docker Compose is enough for this assignment.
