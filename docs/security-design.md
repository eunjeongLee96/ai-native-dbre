# Security Design

## Principle

AI agents should not receive unrestricted database credentials or unrestricted SQL execution capabilities.

## Initial Policy

| Operation | Policy |
|---|---|
| Read metadata | Allow through controlled tools |
| Read performance information | Allow through controlled tools |
| Diagnostic SQL | Allow through predefined/read-only tools |
| Configuration change | Human approval required |
| DDL / destructive operation | Deny by default |
| Credential access | Never expose directly to the model |

## Controls to Explore

- Least-privilege DB accounts
- Tool allowlists
- Input validation
- Query timeout and result limits
- Human-in-the-loop approval
- Audit logs for agent and tool activity
- Secret management
- Network boundaries
- Observability and anomaly detection

This document will evolve as hands-on labs expose additional failure modes and security requirements.
