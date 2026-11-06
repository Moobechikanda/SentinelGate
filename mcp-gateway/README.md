# SentinelGate MCP security gateway

Run from `mcp-gateway` with `MCP_GATEWAY_TOKEN`, `MCP_GATEWAY_SERVERS` (a JSON
object such as `{"github":"https://trusted.example/mcp"}`), then:

```powershell
python -m uvicorn src.gateway:app --host 127.0.0.1 --port 8787
```

`POST /mcp` (or `/gateway`) requires `Authorization: Bearer ...` and a JSON
body containing `server`, `tool`, and an object `arguments`. Optional policy
fields are `action_type`, `resource`, `operation`, `amount`, `currency`,
`supplier_verified`, `approvals`, and `required_approvals`. Destinations are
selected only by the server name and must be in the explicit startup allowlist;
client-supplied URLs are never forwarded. Private destinations require the
explicit `MCP_GATEWAY_ALLOW_PRIVATE_HOSTS=true` setting for local development.

The gateway authenticates, validates, evaluates policy, and only then forwards.
`DENY` and `REQUIRE_APPROVAL` never contact the upstream. Requests and responses
are bounded to 64 KiB, arguments to 32 KiB, and upstream calls to five seconds
by default. Audit records contain no token, URL, or arguments. Direct MCP
connections that bypass this gateway are **not protected** by SentinelGate.

Run tests with `python -m pytest -q`.
