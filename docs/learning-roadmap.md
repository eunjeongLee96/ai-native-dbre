# Learning Roadmap

## Goal

Build enough hands-on understanding to explain and demonstrate how AI agents can safely use database systems.

PostgreSQL is not treated as a separate foundation course. As an experienced MySQL DBA, PostgreSQL concepts will be learned on demand while working through pgvector, DB tools, monitoring, and CloudNativePG labs.

## Phase 1 — pgvector / Vector Search

- Embeddings and similarity search
- Store and query vectors in PostgreSQL
- Distance metrics such as cosine and L2
- HNSW / IVFFlat indexes
- Basic performance experiments

## Phase 2 — RAG

- Prepare database operations documents and runbooks
- Chunk and embed documents
- Store embeddings with pgvector
- Retrieve relevant operational knowledge
- Build a small database-operations RAG pipeline

## Phase 3 — DB Tools

- Tool calling concepts
- Controlled, read-only database interfaces
- DB metadata and health checks
- Connections and lock waits
- Top SQL
- API-based tool integration

## Phase 4 — AI-Native DBRE Agent

- Select appropriate DB tools based on an incident or question
- Gather database evidence
- Retrieve operational knowledge through RAG
- Produce evidence → cause → recommended action
- Integrate selected experiments with an enterprise agent platform where appropriate

## Phase 5 — Guardrails

- Least-privilege database accounts
- Read vs. write tool separation
- Tool allowlists and input validation
- Query timeout and result limits
- Human-in-the-loop approval for state-changing operations
- Audit logging

## Phase 6 — Observability

- Trace agent decisions and tool calls
- Connect agent activity with database state
- Track failures, latency, and abnormal behavior

## Phase 7 — Cloud Native / CloudNativePG

- Container basics as needed
- Kubernetes: Pod, Service, PVC, CRD
- CloudNativePG
- PostgreSQL concepts required for replication and HA
- Failover, backup, PITR, and monitoring

## Scope Rule

This is a breadth-first, use-case-driven lab. PostgreSQL, Kubernetes, and other infrastructure concepts are learned when they become necessary to solve a concrete AI-Native DBRE problem rather than as separate prerequisite courses.
