# SentinelGate backend security foundation

The FastAPI backend persists organizations, memberships, payments, approvals,
idempotency keys, and audit events in SQLite (`SENTINELGATE_DB`, defaulting to
`backend/app/sentinelgate.db`). Tenant and role information is always loaded
from that database; values in request bodies cannot select an organization or
grant permissions.

## Development authentication (not production)

When `SENTINELGATE_ENV` is not `production`, startup seeds a local development
organization and fixed bearer tokens:

* `dev-bootstrap-token` — org-1 admin
* `dev-approver-token` — org-1 approver
* `dev-member-token` — org-1 member
* `dev-other-token` — org-2 admin

Use `Authorization: Bearer <token>` with `/api/*`. These tokens are a
development bootstrap convenience only. Set `SENTINELGATE_ENV=production` and
provide a real token provisioning/authentication integration before deployment;
the seeded tokens must never be used in production.

`/evaluate` remains an unauthenticated deterministic policy simulator for
backwards compatibility. Use `/api/evaluate` for the protected server-context
evaluation path. Payment execution is deliberately simulated and never moves
real funds.
