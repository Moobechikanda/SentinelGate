from __future__ import annotations

import asyncio
import hmac
import ipaddress
import json
import os
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_BODY_BYTES = 64 * 1024
MAX_ARGUMENT_BYTES = 32 * 1024
NAME_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


@dataclass(frozen=True)
class GatewaySettings:
    token: str
    servers: dict[str, str]
    permissions: frozenset[str] = frozenset({"mcp.call"})
    timeout_seconds: float = 5.0
    allow_private_hosts: bool = False
    audit: Callable[[dict[str, Any]], None] | None = None

    @classmethod
    def from_environment(cls) -> "GatewaySettings":
        raw_servers = os.getenv("MCP_GATEWAY_SERVERS", "")
        try:
            servers = json.loads(raw_servers) if raw_servers else {}
        except json.JSONDecodeError as exc:
            raise RuntimeError("MCP_GATEWAY_SERVERS must be JSON") from exc
        token = os.getenv("MCP_GATEWAY_TOKEN", "")
        if not token:
            raise RuntimeError("MCP_GATEWAY_TOKEN is required")
        return cls(
            token=token,
            servers=servers,
            timeout_seconds=float(os.getenv("MCP_GATEWAY_TIMEOUT_SECONDS", "5")),
            allow_private_hosts=os.getenv("MCP_GATEWAY_ALLOW_PRIVATE_HOSTS", "").lower() == "true",
        )

    def validate(self) -> None:
        if not self.token or len(self.token) > 512:
            raise ValueError("a gateway bearer token is required")
        if not self.servers:
            raise ValueError("at least one trusted MCP server is required")
        if not 0 < self.timeout_seconds <= 30:
            raise ValueError("timeout must be between 0 and 30 seconds")
        for name, destination in self.servers.items():
            if not isinstance(name, str) or not NAME_RE.fullmatch(name):
                raise ValueError("invalid trusted server name")
            _validate_destination(destination, self.allow_private_hosts)


def _validate_destination(destination: str, allow_private_hosts: bool) -> None:
    parsed = urllib.parse.urlparse(destination)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("trusted destinations must be absolute HTTP(S) URLs")
    if parsed.username or parsed.password or parsed.fragment or parsed.query:
        raise ValueError("trusted destination contains unsafe URL components")
    if parsed.path not in {"", "/"}:
        raise ValueError("trusted destination must not include a path")
    host = parsed.hostname
    try:
        addresses = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("trusted destination cannot be resolved") from exc
    if not allow_private_hosts:
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified:
                raise ValueError("private or local trusted destinations require explicit opt-in")


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    server: str = Field(min_length=1, max_length=128)
    tool: str = Field(min_length=1, max_length=128)
    arguments: dict[str, Any] = Field(default_factory=dict)
    action_type: str = Field(default="agent.mcp", min_length=1, max_length=128)
    resource: str | None = Field(default=None, max_length=256)
    operation: str = Field(default="call", min_length=1, max_length=64)
    amount: float | None = Field(default=None, ge=0, le=1_000_000_000)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    supplier_verified: bool | None = None
    approvals: int = Field(default=0, ge=0, le=100)
    required_approvals: int = Field(default=1, ge=0, le=100)

    @field_validator("server", "tool", "operation")
    @classmethod
    def valid_name(cls, value: str) -> str:
        if not NAME_RE.fullmatch(value):
            raise ValueError("invalid name")
        return value

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else value


def policy(call: ToolCall, permissions: frozenset[str]) -> tuple[str, str]:
    """Small deterministic fail-closed equivalent of the backend policy rules."""
    resource = call.resource or f"{call.server}:{call.tool}"
    required = f"{resource.split(':')[0]}.{call.operation}" if ":" in resource else call.operation
    if call.required_approvals < call.approvals:
        return "DENY", "Approval state is inconsistent"
    if call.action_type.startswith("finance.") and call.supplier_verified is not True:
        return "DENY", "Supplier is not verified"
    if required not in permissions and call.operation not in permissions and "mcp.call" not in permissions:
        return "DENY", "Actor lacks required permission"
    if "delete" in call.operation or "export" in call.operation:
        return "DENY", "Destructive action denied"
    if call.action_type.startswith("finance.") and call.amount is not None and call.amount > 100:
        needed = 2 if call.amount > 5000 else 1
        if call.approvals < needed:
            return "REQUIRE_APPROVAL", "Payment requires approval"
    if "deploy" in call.operation and call.approvals < 1:
        return "REQUIRE_APPROVAL", "Deployment requires approval"
    return "ALLOW", "Action meets policy rules"


def _default_audit(event: dict[str, Any]) -> None:
    path = os.getenv("MCP_GATEWAY_AUDIT_LOG")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, separators=(",", ":")) + "\n")


def _audit(settings: GatewaySettings, *, server: str, tool: str, decision: str, forwarded: bool, status: str) -> None:
    sink = settings.audit or _default_audit
    sink({"event": "mcp.gateway.call", "server": server, "tool": tool, "decision": decision,
          "forwarded": forwarded, "status": status, "created_at": datetime.now(timezone.utc).isoformat()})


def _forward(destination: str, call: ToolCall, timeout: float) -> tuple[int, bytes]:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": call.tool, "arguments": call.arguments}}).encode()
    request = urllib.request.Request(destination, data=body, method="POST",
                                     headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(MAX_BODY_BYTES + 1)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(MAX_BODY_BYTES + 1)


def create_app(settings: GatewaySettings) -> FastAPI:
    settings.validate()
    app = FastAPI(title="SentinelGate MCP Gateway")

    @app.middleware("http")
    async def limit_body(request: Request, call_next):
        length = request.headers.get("content-length")
        if length and (not length.isdigit() or int(length) > MAX_BODY_BYTES):
            return fastapi_response({"detail": "request too large"}, 413)
        return await call_next(request)

    @app.post("/mcp")
    @app.post("/gateway")
    async def gateway(call_request: Request, authorization: str | None = Header(default=None)):
        if not authorization or not authorization.startswith("Bearer ") or not hmac.compare_digest(
            authorization[7:].strip(), settings.token
        ):
            raise HTTPException(401, "Invalid bearer token", headers={"WWW-Authenticate": "Bearer"})
        try:
            raw = await call_request.body()
            if len(raw) > MAX_BODY_BYTES:
                raise HTTPException(413, "request too large")
            payload = json.loads(raw)
            call = ToolCall.model_validate(payload)
            if len(json.dumps(call.arguments, separators=(",", ":")).encode()) > MAX_ARGUMENT_BYTES:
                raise HTTPException(413, "arguments too large")
        except HTTPException:
            raise
        except (json.JSONDecodeError, TypeError, ValueError):
            raise HTTPException(422, "malformed tool call")
        destination = settings.servers.get(call.server)
        if destination is None:
            _audit(settings, server=call.server, tool=call.tool, decision="DENY", forwarded=False, status="unknown-server")
            raise HTTPException(403, "untrusted MCP server")
        decision, reason = policy(call, settings.permissions)
        if decision != "ALLOW":
            _audit(settings, server=call.server, tool=call.tool, decision=decision, forwarded=False, status="policy-deny")
            return {"decision": decision, "reason": reason, "forwarded": False}
        try:
            status, response_body = await asyncio.to_thread(_forward, destination, call, settings.timeout_seconds)
        except (TimeoutError, socket.timeout):
            _audit(settings, server=call.server, tool=call.tool, decision=decision, forwarded=True, status="timeout")
            raise HTTPException(504, "upstream timeout")
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                _audit(settings, server=call.server, tool=call.tool, decision=decision, forwarded=True, status="timeout")
                raise HTTPException(504, "upstream timeout")
            _audit(settings, server=call.server, tool=call.tool, decision=decision, forwarded=True, status="upstream-error")
            raise HTTPException(502, "upstream unavailable")
        if len(response_body) > MAX_BODY_BYTES:
            raise HTTPException(502, "upstream response too large")
        _audit(settings, server=call.server, tool=call.tool, decision=decision, forwarded=True, status=str(status))
        try:
            response = json.loads(response_body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise HTTPException(502, "upstream returned invalid JSON")
        return {"decision": decision, "forwarded": True, "upstream_status": status, "response": response}

    return app


def fastapi_response(content: dict[str, Any], status_code: int):
    from fastapi.responses import JSONResponse
    return JSONResponse(content, status_code=status_code)


app = create_app(GatewaySettings.from_environment()) if os.getenv("MCP_GATEWAY_TOKEN") else None
