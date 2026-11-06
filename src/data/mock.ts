import type { Agent, Tool, Supplier, Invoice, Transaction, AuditEvent, Policy } from "../types";

export const agents: Agent[] = [
  { id: "ag-1", name: "Finance Assistant", type: "Finance Agent", env: "Production", status: "Active", owner: "Finance Team", capabilities: ["finance.invoice.read", "finance.payment.prepare"] },
  { id: "ag-2", name: "Customer Support Agent", type: "Customer Support Agent", env: "Production", status: "Active", owner: "Support Team", capabilities: ["email.read", "email.send"] },
  { id: "ag-3", name: "Coding Assistant", type: "AI Coding Agent", env: "Staging", status: "Active", owner: "Engineering", capabilities: ["github.repository.read", "github.repository.write"] },
];

export const tools: Tool[] = [
  { id: "t-1", name: "Accounting System", category: "Finance", risk: "HIGH", status: "Connected", operations: ["read", "prepare", "execute"] },
  { id: "t-2", name: "GitHub", category: "Development", risk: "MEDIUM", status: "Connected", operations: ["read", "write", "deploy"] },
  { id: "t-3", name: "Email", category: "Communication", risk: "MEDIUM", status: "Connected", operations: ["read", "send"] },
  { id: "t-4", name: "Database", category: "Data", risk: "HIGH", status: "Connected", operations: ["read", "write", "delete"] },
  { id: "t-5", name: "Deployment Platform", category: "Deployment", risk: "CRITICAL", status: "Connected", operations: ["deploy"] },
];

export const suppliers: Supplier[] = [
  { id: "s-1", name: "Copperfield Supplies Ltd", code: "COP-001", country: "Zambia", bankName: "Zanaco", accountName: "Copperfield Supplies Ltd", accountNumber: "****4521", currency: "ZMW", verification: "VERIFIED" },
  { id: "s-2", name: "Lusaka Industrial Traders", code: "LIT-002", country: "Zambia", bankName: "Stanbic", accountName: "Lusaka Industrial Traders", accountNumber: "****8834", currency: "ZMW", verification: "VERIFIED" },
  { id: "s-3", name: "Southern Equipment Ltd", code: "SEL-003", country: "Zambia", bankName: "FNB", accountName: "Southern Equipment Ltd", accountNumber: "****1102", currency: "ZMW", verification: "UNVERIFIED" },
];

export const invoices: Invoice[] = [
  { id: "inv-1", number: "INV-001", supplierId: "s-1", amount: 5000, currency: "ZMW", date: "2026-10-01", dueDate: "2026-10-31", status: "APPROVED" },
  { id: "inv-2", number: "INV-002", supplierId: "s-2", amount: 25000, currency: "ZMW", date: "2026-10-05", dueDate: "2026-11-05", status: "SUBMITTED" },
  { id: "inv-3", number: "INV-003", supplierId: "s-3", amount: 12000, currency: "ZMW", date: "2026-10-10", dueDate: "2026-11-10", status: "SUBMITTED" },
  { id: "inv-4", number: "INV-004", supplierId: "s-1", amount: 8000, currency: "ZMW", date: "2026-10-12", dueDate: "2026-11-12", status: "SUBMITTED" },
];

export const transactions: Transaction[] = [
  { id: "tx-1", supplierId: "s-1", invoiceId: "inv-1", amount: 5000, currency: "ZMW", description: "Payment for INV-001", status: "APPROVED", approvals: 1, requiredApprovals: 1, requester: "Finance Manager" },
  { id: "tx-2", supplierId: "s-2", invoiceId: "inv-2", amount: 25000, currency: "ZMW", description: "Payment for INV-002", status: "PENDING", approvals: 0, requiredApprovals: 2, requester: "Finance Manager" },
  { id: "tx-3", supplierId: "s-3", invoiceId: "inv-3", amount: 12000, currency: "ZMW", description: "Payment for INV-003", status: "PENDING", approvals: 0, requiredApprovals: 1, requester: "Finance Manager" },
  { id: "tx-4", supplierId: "s-1", invoiceId: "inv-4", amount: 8000, currency: "ZMW", description: "Duplicate invoice payment", status: "PENDING", approvals: 0, requiredApprovals: 1, requester: "Finance Manager" },
];

export const auditEvents: AuditEvent[] = [
  { id: "ae-1", timestamp: "2026-10-15T09:00:00Z", actor: "Finance Assistant", type: "agent_action", resource: "invoice INV-001", decision: "ALLOW", risk: "LOW", reason: "Agent has read permission" },
  { id: "ae-2", timestamp: "2026-10-15T09:05:00Z", actor: "Coding Assistant", type: "agent_action", resource: "repository delete", decision: "DENY", risk: "HIGH", reason: "No delete permission" },
  { id: "ae-3", timestamp: "2026-10-15T09:10:00Z", actor: "Coding Assistant", type: "agent_action", resource: "production deploy", decision: "REQUIRE_APPROVAL", risk: "CRITICAL", reason: "Production deployment requires approval" },
  { id: "ae-4", timestamp: "2026-10-15T09:15:00Z", actor: "Unknown Agent", type: "agent_action", resource: "customer records export", decision: "DENY", risk: "CRITICAL", reason: "Unknown agent has no permissions" },
  { id: "ae-5", timestamp: "2026-10-15T09:20:00Z", actor: "Finance Manager", type: "bank_change", resource: "supplier Southern Equipment", decision: "HOLD_FOR_VERIFICATION", risk: "HIGH", reason: "Bank detail change requires independent verification" },
];

export const policies: Policy[] = [
  { id: "p-1", name: "Agent tool access", category: "Agent permissions", description: "Agents may only access explicitly authorized tools", decision: "DENY", status: "Enabled", version: 1 },
  { id: "p-2", name: "Production deployment", category: "Deployment controls", description: "Production deployments require approval", decision: "REQUIRE_APPROVAL", status: "Enabled", version: 1 },
  { id: "p-3", name: "Supplier verification", category: "Supplier verification", description: "Unverified suppliers cannot receive approved payments", decision: "DENY", status: "Enabled", version: 1 },
  { id: "p-4", name: "Bank detail changes", category: "Supplier verification", description: "Bank detail changes require independent verification", decision: "HOLD_FOR_VERIFICATION", status: "Enabled", version: 1 },
  { id: "p-5", name: "Payment threshold", category: "Financial thresholds", description: "Payments above threshold require two approvers", decision: "REQUIRE_APPROVAL", status: "Enabled", version: 1 },
  { id: "p-6", name: "Data export", category: "Data access", description: "Agents cannot export sensitive data without authorization", decision: "DENY", status: "Enabled", version: 1 },
];
