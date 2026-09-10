# Learning Roadmap

## Goal

Build enough hands-on understanding to explain and demonstrate how AI agents can safely use database systems.

## Phase 1 — PostgreSQL Foundation

- PostgreSQL architecture and basic administration
- Important behavioral differences from MySQL
- Roles and privileges
- Transactions and locking
- Monitoring and query analysis

## Phase 2 — Vector Search and RAG

- Embeddings and similarity search
- pgvector
- Distance metrics and indexes
- Build a small RAG pipeline using database operations documentation

## Phase 3 — Agent + Database Tools

- Tool calling concepts
- Read-only diagnostic tools
- DB metadata and health checks
- Top SQL / connections / locks
- API-based tool integration
- HelpNow Foundry workflow experiments

## Phase 4 — Safety and Observability

- Least privilege
- Read vs. write tool separation
- Human-in-the-loop approval
- Audit logging
- Agent/tool observability

## Phase 5 — Cloud Native Database

- Container basics
- Kubernetes: Pod, Service, PVC, CRD
- CloudNativePG
- Failover, backup, recovery, and monitoring concepts

## Scope Rule

This is a breadth-first lab. The goal is not to become an expert in every technology within three months. Each technology is introduced when it solves a concrete problem in the AI-Native DBRE architecture.
