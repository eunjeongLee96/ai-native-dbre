# AI-Native DBRE Lab

Building safe and observable database interfaces for AI agents.

This lab explores how AI agents can safely understand, observe, diagnose, and interact with databases using controlled tools, RAG, vector search, guardrails, and cloud-native database patterns.

## Focus

- PostgreSQL for a MySQL DBA
- pgvector and vector search
- RAG for database operations knowledge
- AI Agent tool calling
- MCP / API integration
- Security, guardrails, and human approval
- Observability for agent-driven DB operations
- CloudNativePG and Kubernetes fundamentals
- Graph DB exploration for fraud transaction networks
- HelpNow Foundry as the enterprise agent platform used for selected experiments

## Guiding Principle

> AI should not receive unrestricted database access.
>
> The goal is to design controlled, observable, least-privilege interfaces that allow AI agents to work with database systems safely.

## AI-Native DBRE Architecture

```text
Bespin Global HelpNow / Foundry
              │
              ▼
       AI-Native DBRE Agent
              │
      ┌───────┼──────────┐
      ▼       ▼          ▼
   DB Tools   RAG     Guardrails
      │       │          │
      ▼       ▼          │
 PostgreSQL  pgvector    │
 MySQL/RDS               │
      │                  │
      └────────┬─────────┘
               ▼
     Observability / Cloud Native
```

## Repository Structure

```text
ai-native-dbre/
├── docs/
├── postgresql/
│   ├── labs/
│   └── sql/
├── vector/
│   ├── pgvector-lab/
│   └── rag-lab/
├── graph/
│   └── fraud-transaction-network/
├── agent/
│   ├── db-tools/
│   ├── prompts/
│   └── workflows/
├── mcp/
├── observability/
└── cloud-native/
    └── cnpg/
```

## Separate Lab: Graph DB / Fraud Transaction Network

After the pgvector/vector-search exercises, a separate graph database lab will reuse the account-to-account transaction data from the existing GAT/GATv2 fraud detection experiments.

```text
Graph DB / Fraud Transaction Network
├── Account nodes
├── Transaction edges
├── fraud label
├── amount / timestamp
├── degree / community
└── path / neighborhood exploration
```

The purpose is to explore relationship-oriented questions such as direct neighbors, multi-hop transaction paths, and neighborhoods around fraud-labeled accounts. Graph DB exploration will remain separate from vector similarity search, while a future extension may connect GAT-generated node embeddings to pgvector.

## Project Goal

Move from traditional DBA automation toward **AI-Native Database Reliability Engineering**: designing systems where AI agents can use databases safely, with explicit permissions, traceable actions, and human control over risky changes.

## Status

Work in progress — labs and architecture notes will be added incrementally.
