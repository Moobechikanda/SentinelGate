const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "sentinelgate.access_token";

export type AuditEventResponse = {
  id: number;
  actor_id: string;
  event_type: string;
  details: string;
  created_at: string;
};

export type PolicyDecision = {
  decision: string;
  risk_level: string;
  reason: string;
  matched_policies: string[];
  approval_required: boolean;
  approval_count_required: number;
  evaluated_at: string;
};

export type ProtectedAction = {
  action_type: string;
  resource: string;
  operation: string;
  amount?: number;
  currency?: string;
  supplier_verified?: boolean;
};

export type PaymentRequest = {
  id: string;
  amount: number;
  currency: string;
  supplier_verified: boolean;
};

export type PaymentResponse = {
  id: string;
  status: string;
  required_approvals?: number;
  approval_count?: number;
  simulated?: boolean;
};

export class ApiError extends Error {
  readonly status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export const tokenStorage = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = tokenStorage.get();
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError("Unable to reach the SentinelGate API.", 0);
  }

  if (!response.ok) {
    let message = `API request failed (${response.status}).`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) message = body.detail;
    } catch {
      // Keep the generic, non-sensitive message.
    }
    throw new ApiError(message, response.status);
  }
  return (await response.json()) as T;
}

export const api = {
  getAudit: () => request<AuditEventResponse[]>("/api/audit"),
  evaluate: (action: ProtectedAction) =>
    request<PolicyDecision>("/api/evaluate", {
      method: "POST",
      body: JSON.stringify(action),
    }),
  createPayment: (payment: PaymentRequest) =>
    request<PaymentResponse>("/api/payments", {
      method: "POST",
      body: JSON.stringify(payment),
    }),
  approvePayment: (id: string) =>
    request<PaymentResponse>(`/api/payments/${encodeURIComponent(id)}/approve`, { method: "POST" }),
  executePayment: (id: string, idempotencyKey: string) =>
    request<PaymentResponse>(`/api/payments/${encodeURIComponent(id)}/execute`, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
    }),
};

