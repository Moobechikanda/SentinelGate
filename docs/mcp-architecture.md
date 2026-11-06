# SentinelGate MCP Gateway Architecture

## Borrowed from Docker MCP Gateway
- MCP client/server connections via stdio/SSE transports
- Tool discovery and registration
- Interception point before forwarding tool calls
- Secret scanning on tool arguments/responses
- Policy enforcement consistent across tool calls

## From Microsoft Agent Governance Toolkit
- Agent identity and permissions
- Runtime governance and human intervention
- Audit trails for tool execution

## From OPA
- Formal policy evaluation (Rego) - future replacement of deterministic rules

## From Official MCP Python SDK
- Client/server SDK for Python integration

## From OWASP MCP Security Testing Guide
- Threat model, attack patterns, testing checklists

## Integration Plan
1. Build separate gateway service (Python) that authenticates agents
2. Connect to trusted MCP servers
3. Discover tools, intercept calls
4. Evaluate each call via SentinelGate policy engine (/evaluate)
5. Deny unauthorized, pause sensitive for approval
6. Inspect responses for sensitive data
7. Record audit events

## Default: deny. No fake connections in MVP.
