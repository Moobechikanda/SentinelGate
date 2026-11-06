# SentinelGate threat model

## Assets

- Organization records and membership assignments.
- Agent credentials, tool permissions, and policy definitions.
- Supplier bank details, invoices, payment requests, and approvals.
- Audit events and policy evaluation history.
- MCP credentials, tool arguments, and tool responses.

## Trust boundaries

1. Browser to API: the browser is untrusted and may modify every request field.
2. API to persistence: authorization and tenant scope must be established before queries or writes.
3. Gateway to upstream MCP server: only configured, trusted destinations may be reached.
4. Operator to control plane: privileged changes require explicit authorization and audit records.
5. Development to production: development tokens, data, and services must never be promoted.

## Primary threats and controls

| Threat | Required control |
|---|---|
| Cross-tenant data access | Server-derived organization context, repository scoping, database RLS |
| Privilege escalation | Server-side RBAC, least privilege, MFA, dual control, audit |
| Forged policy decision | Evaluate only on the server; deny on evaluation failure |
| Duplicate payment | Idempotency key, unique constraint, transaction, immutable execution record |
| Unauthorized bank change | Independent verification, hold affected payments, history |
| MCP SSRF or bypass | Destination allowlist, private-address rejection, gateway-only deployment |
| Prompt/tool injection | Deterministic policy checks, argument validation, no model override of DENY |
| Secret leakage | Secret redaction, no frontend service credentials, bounded audit payloads |
| Availability attack | WAF, rate limits, timeouts, body limits, circuit breakers |
| Evidence destruction | Append-only/remote audit sink, restricted deletion, retention controls |

## Residual risk

The local MVP still requires production identity, PostgreSQL RLS, hardened deployment, centralized logging, and independent testing before it can be used for real government or institutional data.
