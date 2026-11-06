# SentinelGate security operations baseline

SentinelGate is a security-control MVP, not a certification. Government or regulated-institution deployment requires an independent threat model, penetration test, privacy review, accessibility review, disaster-recovery exercise, and formal authorization to operate.

## Protected execution paths

- Authenticated API requests derive the actor and organization from server-side authentication state.
- Tenant-scoped records are filtered by the authenticated organization; client-supplied organization identifiers are not authorization.
- Policy decisions default to deny when authorization context is missing or inconsistent.
- Approval-required actions are not executed until the approval transition succeeds.
- Simulated payment execution is idempotent and never calls a banking rail.
- MCP calls must pass through the gateway to receive authentication, destination validation, argument limits, policy evaluation, timeout handling, and audit recording.

Direct database access, direct MCP connections, development bootstrap tokens, and any endpoint exposed without the configured authentication middleware are outside the protected boundary.

## Production controls required before institutional use

1. Replace development bootstrap authentication with an approved OIDC/SAML provider, MFA, short-lived tokens, key rotation, and hardware-backed administrator credentials.
2. Deploy PostgreSQL/Supabase with private networking, encryption, backups, point-in-time recovery, tested RLS policies, and separate projects for development, staging, and production.
3. Store secrets in a managed secret store. Never place service-role credentials, signing keys, or bank data in frontend bundles or logs.
4. Put the API and gateway behind a WAF/API gateway with TLS, request-size limits, rate limits, DDoS controls, network egress policy, and centralized security monitoring.
5. Centralize immutable audit logs in a write-only sink with retention, time synchronization, access review, and alerting for privilege changes, denied actions, approval changes, and gateway bypass attempts.
6. Require dual control for policy, role, supplier-bank, and payment-control changes. Record who requested, approved, executed, and reviewed each change.
7. Run dependency scanning, static analysis, secret scanning, container/image scanning, dynamic testing, penetration testing, and restore drills in CI/CD.
8. Establish incident response, vulnerability disclosure, access review, key rotation, data retention/deletion, and business-continuity procedures.

## Security test minimum

- Authentication failure and token expiry.
- Cross-tenant reads and writes.
- Role escalation and self-approval.
- Suspended/revoked actors and unknown tools.
- Duplicate and replayed payment execution.
- Concurrent approval and execution races.
- Malformed/oversized requests and rate limiting.
- SSRF, private destination, redirect, timeout, and response-size controls in the gateway.
- Secret leakage in audit logs and error responses.
- Backup restore and audit-log continuity.

Passing local tests demonstrates behavior of this checkout only; it is not evidence of compliance with a government or institutional framework.
