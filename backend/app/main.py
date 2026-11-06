"""SentinelGate API.

The ``/evaluate`` route is retained as a deterministic, unauthenticated policy
simulation for backwards compatibility. All state-changing and tenant-aware
routes live under ``/api`` and derive identity, organization and permissions
from the local server database.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, List, Literal, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

DB_PATH = os.getenv("SENTINELGATE_DB", os.path.join(os.path.dirname(__file__), "sentinelgate.db"))
ENVIRONMENT = os.getenv("SENTINELGATE_ENV", "development").lower()
DEV_TOKEN = os.getenv("SENTINELGATE_DEV_TOKEN", "dev-bootstrap-token")
DB_LOCK = threading.RLock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class Database:
    """Small tenant-scoped sqlite repository using only the standard library."""

    def __init__(self, path: str = DB_PATH):
        self.path = path
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with DB_LOCK, self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS organizations (id TEXT PRIMARY KEY, name TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, token_hash TEXT UNIQUE NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memberships (
                    organization_id TEXT NOT NULL REFERENCES organizations(id),
                    user_id TEXT NOT NULL REFERENCES users(id),
                    role TEXT NOT NULL CHECK(role IN ('admin','approver','member','viewer')),
                    permissions TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (organization_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, organization_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL, event_type TEXT NOT NULL, details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS payments (
                    id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, amount REAL NOT NULL,
                    currency TEXT NOT NULL, supplier_verified INTEGER NOT NULL,
                    status TEXT NOT NULL, required_approvals INTEGER NOT NULL,
                    created_by TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS payment_approvals (
                    payment_id TEXT NOT NULL REFERENCES payments(id),
                    actor_id TEXT NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY(payment_id, actor_id)
                );
                CREATE TABLE IF NOT EXISTS idempotency_keys (
                    organization_id TEXT NOT NULL, actor_id TEXT NOT NULL, key TEXT NOT NULL,
                    request_hash TEXT NOT NULL, response TEXT NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY(organization_id, actor_id, key)
                );
                """
            )
            if ENVIRONMENT != "production":
                self._bootstrap(db)

    def _bootstrap(self, db: sqlite3.Connection) -> None:
        db.execute("INSERT OR IGNORE INTO organizations VALUES (?, ?)", ("org-1", "Development Organization"))
        db.execute("INSERT OR IGNORE INTO organizations VALUES (?, ?)", ("org-2", "Second Development Organization"))
        users = [
            ("user-admin", "Development Admin", DEV_TOKEN),
            ("user-approver", "Development Approver", "dev-approver-token"),
            ("user-member", "Development Member", "dev-member-token"),
            ("user-other", "Other Organization User", "dev-other-token"),
        ]
        for user_id, name, token in users:
            db.execute(
                "INSERT OR IGNORE INTO users(id,name,token_hash) VALUES(?,?,?)",
                (user_id, name, token_hash(token)),
            )
        memberships = [
            ("org-1", "user-admin", "admin", "finance.execute,finance.approve,agent.read"),
            ("org-1", "user-approver", "approver", "finance.approve,agent.read"),
            ("org-1", "user-member", "member", "agent.read"),
            ("org-2", "user-other", "admin", "finance.execute,finance.approve"),
        ]
        for membership in memberships:
            db.execute(
                "INSERT OR IGNORE INTO memberships(organization_id,user_id,role,permissions) VALUES(?,?,?,?)",
                membership,
            )

    def actor(self, raw_token: str) -> Optional[dict[str, Any]]:
        with DB_LOCK, self.connect() as db:
            row = db.execute(
                """SELECT u.id, u.name, m.organization_id, m.role, m.permissions
                   FROM users u JOIN memberships m ON m.user_id=u.id
                   WHERE u.token_hash=?""",
                (token_hash(raw_token),),
            ).fetchone()
        if not row:
            return None
        return {**dict(row), "permissions": [p for p in row["permissions"].split(",") if p]}

    def audit(self, organization_id: str, actor_id: str, event_type: str, details: str) -> None:
        with DB_LOCK, self.connect() as db:
            db.execute(
                "INSERT INTO audit_events(organization_id,actor_id,event_type,details,created_at) VALUES(?,?,?,?,?)",
                (organization_id, actor_id, event_type, details[:4000], now()),
            )


db = Database()


class ActionRequest(BaseModel):
    organization_id: str = Field(min_length=1, max_length=128)
    actor_type: Literal["agent", "user"]
    actor_id: str = Field(min_length=1, max_length=128)
    action_type: str = Field(min_length=1, max_length=128)
    resource: str = Field(min_length=1, max_length=256)
    operation: str = Field(min_length=1, max_length=64)
    amount: Optional[float] = Field(default=None, ge=0, le=1_000_000_000)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    supplier_verified: Optional[bool] = None
    approvals: int = Field(default=0, ge=0, le=100)
    required_approvals: int = Field(default=1, ge=0, le=100)
    permissions: List[str] = Field(default_factory=list, max_length=100)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: Optional[str]) -> Optional[str]:
        return value.upper() if value else value

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, values: List[str]) -> List[str]:
        if any(not permission or len(permission) > 128 for permission in values):
            raise ValueError("permissions must contain non-empty values up to 128 characters")
        return values


class PolicyDecision(BaseModel):
    decision: str
    risk_level: str
    reason: str
    matched_policies: List[str]
    approval_required: bool
    approval_count_required: int
    evaluated_at: str


def evaluate(request: ActionRequest) -> PolicyDecision:
    matched = []
    decision, risk, reason, approvals_needed = "DENY", "MEDIUM", "No applicable policy; default deny", 0
    if request.required_approvals < request.approvals:
        matched.append("invalid-approval-state")
        return PolicyDecision(decision="DENY", risk_level="HIGH", reason="Approval state is inconsistent",
                              matched_policies=matched, approval_required=False, approval_count_required=0, evaluated_at=now())
    perm = f"{request.resource.split(':')[0]}.{request.operation}" if ":" in request.resource else request.operation
    has_perm = perm in request.permissions or request.operation in request.permissions
    if request.action_type.startswith("finance."):
        if request.supplier_verified is not True:
            matched.append("supplier-verification")
            return PolicyDecision(decision="DENY", risk_level="HIGH", reason="Supplier is not verified",
                                  matched_policies=matched, approval_required=False, approval_count_required=0, evaluated_at=now())
        if request.amount is not None and request.amount > 1000:
            matched.append("payment-threshold")
            approvals_needed = 2 if request.amount > 5000 else 1
            if request.approvals < approvals_needed:
                return PolicyDecision(decision="REQUIRE_APPROVAL", risk_level="HIGH", reason="Amount exceeds approval threshold",
                                      matched_policies=matched, approval_required=True, approval_count_required=approvals_needed, evaluated_at=now())
        if request.amount is not None and request.amount > 100 and request.approvals < 1:
            matched.append("payment-approval")
            return PolicyDecision(decision="REQUIRE_APPROVAL", risk_level="MEDIUM", reason="Payment requires approval",
                                  matched_policies=matched, approval_required=True, approval_count_required=1, evaluated_at=now())
    if request.actor_type == "agent":
        if not has_perm:
            matched.append("agent-permission")
            return PolicyDecision(decision="DENY", risk_level="HIGH", reason="Agent lacks required permission",
                                  matched_policies=matched, approval_required=False, approval_count_required=0, evaluated_at=now())
        if "deploy" in request.operation and request.approvals < 1:
            matched.append("deployment-control")
            return PolicyDecision(decision="REQUIRE_APPROVAL", risk_level="CRITICAL", reason="Deployment requires approval",
                                  matched_policies=matched, approval_required=True, approval_count_required=1, evaluated_at=now())
        if "delete" in request.operation or "export" in request.operation:
            matched.append("destructive-action")
            return PolicyDecision(decision="DENY", risk_level="CRITICAL", reason="Destructive action denied",
                                  matched_policies=matched, approval_required=False, approval_count_required=0, evaluated_at=now())
    if request.actor_type == "user" and not request.actor_id:
        matched.append("actor-identity")
        return PolicyDecision(decision="DENY", risk_level="HIGH", reason="Actor identity is required",
                              matched_policies=matched, approval_required=False, approval_count_required=0, evaluated_at=now())
    matched.append("default-allow")
    return PolicyDecision(decision="ALLOW", risk_level="LOW", reason="Action meets policy rules",
                          matched_policies=matched, approval_required=False, approval_count_required=0, evaluated_at=now())


app = FastAPI(title="SentinelGate Policy Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in os.getenv("SENTINELGATE_CORS_ORIGINS", "http://localhost:5173").split(",") if o],
    allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)
_rate_windows: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if request.headers.get("content-length") and int(request.headers["content-length"]) > 1_048_576:
        return JSONResponse({"detail": "request too large"}, status_code=413)
    key = request.client.host if request.client else "unknown"
    window = _rate_windows[key]
    current = time.monotonic()
    while window and current - window[0] > 60:
        window.popleft()
    if len(window) >= 120:
        return JSONResponse({"detail": "rate limit exceeded"}, status_code=429, headers={"Retry-After": "60"})
    window.append(current)
    response = await call_next(request)
    response.headers.update({"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
                             "Referrer-Policy": "no-referrer", "Content-Security-Policy": "default-src 'none'",
                             "Cache-Control": "no-store"})
    return response


def current_actor(authorization: Optional[str] = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Bearer authentication required", headers={"WWW-Authenticate": "Bearer"})
    actor = db.actor(authorization[7:].strip())
    if not actor:
        raise HTTPException(401, "Invalid bearer token", headers={"WWW-Authenticate": "Bearer"})
    return actor


def require_permission(permission: str):
    def dependency(actor: dict[str, Any] = Depends(current_actor)) -> dict[str, Any]:
        if permission not in actor["permissions"] and actor["role"] != "admin":
            raise HTTPException(403, "Insufficient permission")
        return actor
    return dependency


@app.post("/evaluate", response_model=PolicyDecision)
def evaluate_action(req: ActionRequest):
    return evaluate(req)


class ProtectedAction(BaseModel):
    action_type: str = Field(min_length=1, max_length=128)
    resource: str = Field(min_length=1, max_length=256)
    operation: str = Field(min_length=1, max_length=64)
    amount: Optional[float] = Field(default=None, ge=0, le=1_000_000_000)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    supplier_verified: Optional[bool] = None


@app.post("/api/evaluate", response_model=PolicyDecision)
def protected_evaluate(req: ProtectedAction, actor: dict[str, Any] = Depends(current_actor)):
    required_permission = f"{req.resource.split(':')[0]}.{req.operation}" if ":" in req.resource else req.operation
    if required_permission not in actor["permissions"] and req.operation not in actor["permissions"] and actor["role"] != "admin":
        result = PolicyDecision(decision="DENY", risk_level="HIGH", reason="Actor lacks required permission",
                                matched_policies=["server-rbac"], approval_required=False,
                                approval_count_required=0, evaluated_at=now())
        db.audit(actor["organization_id"], actor["id"], "policy.evaluated", result.decision)
        return result
    approvals = 0
    internal = ActionRequest(
        organization_id=actor["organization_id"], actor_type="user", actor_id=actor["id"],
        action_type=req.action_type, resource=req.resource, operation=req.operation, amount=req.amount,
        currency=req.currency, supplier_verified=req.supplier_verified, approvals=approvals,
        permissions=actor["permissions"],
    )
    result = evaluate(internal)
    db.audit(actor["organization_id"], actor["id"], "policy.evaluated", result.decision)
    return result


class PaymentCreate(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    amount: float = Field(gt=0, le=1_000_000_000)
    currency: str = Field(min_length=3, max_length=3)
    supplier_verified: bool

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, value: str) -> str:
        return value.upper()


@app.post("/api/payments")
def create_payment(req: PaymentCreate, actor: dict[str, Any] = Depends(require_permission("finance.execute"))):
    if req.supplier_verified is not True:
        raise HTTPException(422, "supplier must be verified")
    required = 2 if req.amount > 5000 else (1 if req.amount > 100 else 0)
    with DB_LOCK, db.connect() as connection:
        try:
            connection.execute(
                "INSERT INTO payments VALUES(?,?,?,?,?,?,?,?,?)",
                (req.id, actor["organization_id"], req.amount, req.currency, int(req.supplier_verified),
                 "APPROVED" if required == 0 else "PENDING", required, actor["id"], now()),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(409, "payment already exists")
    db.audit(actor["organization_id"], actor["id"], "payment.created", req.id)
    return {"id": req.id, "status": "APPROVED" if required == 0 else "PENDING",
            "required_approvals": required}


@app.post("/api/payments/{payment_id}/approve")
def approve_payment(payment_id: str, actor: dict[str, Any] = Depends(require_permission("finance.approve"))):
    with DB_LOCK, db.connect() as connection:
        payment = connection.execute("SELECT * FROM payments WHERE id=? AND organization_id=?",
                                     (payment_id, actor["organization_id"])).fetchone()
        if not payment:
            raise HTTPException(404, "payment not found")
        if payment["status"] == "EXECUTED":
            raise HTTPException(409, "payment already executed")
        connection.execute("INSERT OR IGNORE INTO payment_approvals VALUES(?,?,?)",
                           (payment_id, actor["id"], now()))
        count = connection.execute("SELECT COUNT(*) FROM payment_approvals WHERE payment_id=?",
                                   (payment_id,)).fetchone()[0]
        status = "APPROVED" if count >= payment["required_approvals"] else "PENDING"
        connection.execute("UPDATE payments SET status=? WHERE id=?", (status, payment_id))
    db.audit(actor["organization_id"], actor["id"], "payment.approved", payment_id)
    return {"id": payment_id, "status": status, "approval_count": count}


@app.post("/api/payments/{payment_id}/execute")
def execute_payment(payment_id: str, idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
                    actor: dict[str, Any] = Depends(require_permission("finance.execute"))):
    if not idempotency_key or len(idempotency_key) > 128:
        raise HTTPException(400, "Idempotency-Key header is required")
    with DB_LOCK, db.connect() as connection:
        payment = connection.execute("SELECT * FROM payments WHERE id=? AND organization_id=?",
                                     (payment_id, actor["organization_id"])).fetchone()
        if not payment:
            raise HTTPException(404, "payment not found")
        request_hash = hashlib.sha256(f"{payment_id}:{payment['amount']}:{payment['currency']}".encode()).hexdigest()
        existing = connection.execute(
            "SELECT request_hash,response FROM idempotency_keys WHERE organization_id=? AND actor_id=? AND key=?",
            (actor["organization_id"], actor["id"], idempotency_key)).fetchone()
        if existing:
            if existing["request_hash"] != request_hash:
                raise HTTPException(409, "idempotency key was reused for another request")
            import json
            return json.loads(existing["response"])
        if payment["status"] != "APPROVED":
            raise HTTPException(409, "payment requires approval")
        connection.execute("UPDATE payments SET status='EXECUTED' WHERE id=? AND status='APPROVED'", (payment_id,))
        result = {"id": payment_id, "status": "EXECUTED", "simulated": True}
        import json
        connection.execute("INSERT INTO idempotency_keys VALUES(?,?,?,?,?,?)",
                           (actor["organization_id"], actor["id"], idempotency_key, request_hash,
                            json.dumps(result), now()))
    db.audit(actor["organization_id"], actor["id"], "payment.executed.simulated", payment_id)
    return result


@app.get("/api/audit")
def audit_events(actor: dict[str, Any] = Depends(current_actor)):
    with DB_LOCK, db.connect() as connection:
        rows = connection.execute(
            "SELECT id,actor_id,event_type,details,created_at FROM audit_events WHERE organization_id=? ORDER BY id DESC LIMIT 100",
            (actor["organization_id"],)).fetchall()
    return [dict(row) for row in rows]


@app.get("/health")
def health():
    return {"status": "ok", "service": "SentinelGate Policy Engine"}
