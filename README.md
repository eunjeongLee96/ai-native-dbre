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
├── agent/
│   ├── db-tools/
│   ├── prompts/
│   └── workflows/
├── mcp/
├── observability/
└── cloud-native/
    └── cnpg/
```

## Project Goal

Move from traditional DBA automation toward **AI-Native Database Reliability Engineering**: designing systems where AI agents can use databases safely, with explicit permissions, traceable actions, and human control over risky changes.

## Status

Work in progress — labs and architecture notes will be added incrementally.
