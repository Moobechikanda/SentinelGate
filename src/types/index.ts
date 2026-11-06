export type Decision = "ALLOW" | "DENY" | "REQUIRE_APPROVAL" | "HOLD_FOR_VERIFICATION";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type Role = "SUPER_ADMIN" | "ORGANIZATION_ADMIN" | "SECURITY_ADMIN" | "FINANCE_MANAGER" | "APPROVER" | "AUDITOR" | "EMPLOYEE";
export type AgentStatus = "Active" | "Suspended" | "Revoked";
export type AgentType = "AI Coding Agent" | "Customer Support Agent" | "Finance Agent" | "Research Agent" | "General Purpose Agent" | "Custom Agent";
export type AgentEnv = "Development" | "Testing" | "Staging" | "Production";
export type SupplierVerification = "UNVERIFIED" | "PENDING_VERIFICATION" | "VERIFIED" | "SUSPENDED";
export type InvoiceStatus = "DRAFT" | "SUBMITTED" | "APPROVED" | "REJECTED" | "PAID" | "CANCELLED";
export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED" | "CANCELLED";

export interface Agent { id: string; name: string; type: AgentType; env: AgentEnv; status: AgentStatus; owner: string; capabilities: string[]; }
export interface Tool { id: string; name: string; category: string; risk: RiskLevel; status: string; operations: string[]; }
export interface Supplier { id: string; name: string; code: string; country: string; bankName: string; accountName: string; accountNumber: string; currency: string; verification: SupplierVerification; }
export interface Invoice { id: string; number: string; supplierId: string; amount: number; currency: string; date: string; dueDate: string; status: InvoiceStatus; }
export interface Transaction { id: string; supplierId: string; invoiceId?: string; amount: number; currency: string; description: string; status: ApprovalStatus; approvals: number; requiredApprovals: number; requester: string; }
export interface AuditEvent { id: string; timestamp: string; actor: string; type: string; resource: string; decision: Decision; risk: RiskLevel; reason: string; }
export interface Policy { id: string; name: string; category: string; description: string; decision: Decision; status: "Enabled" | "Disabled"; version: number; }
