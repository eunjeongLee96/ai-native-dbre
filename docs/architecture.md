# Architecture

## Target Architecture

```text
                  Enterprise AI Agent Platform
                       (HelpNow Foundry)
                              │
                        AI DBRE Agent
                              │
              ┌───────────────┼───────────────┐
              │               │               │
           DB Tools        Knowledge        Guardrails
              │               │               │
         Tool / API          RAG       Least Privilege
              │               │        Human Approval
              │           pgvector          Audit
              │               │               │
              └───────────────┼───────────────┘
                              │
                   PostgreSQL / MySQL / RDS
                              │
                       Observability
                              │
                  CloudNativePG / K8s
```

## Evolution

### V1 — Provisioning Automation

Natural language → Agent → Terraform → GitHub → GitHub Actions → AWS RDS

### V2 — AI-Native DBRE

The next step is not simply adding more provisioning actions. The goal is to let an agent safely observe database state, select appropriate diagnostic tools, gather evidence, use operational knowledge, and recommend or perform controlled actions.

## Design Rule

Read and diagnostic operations should be separated from state-changing operations. Risky changes require explicit controls such as human approval, least-privilege credentials, and audit trails.
