import { useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../api/client";
import type { PolicyDecision } from "../api/client";

export default function PolicySimulator() {
  const [action, setAction] = useState("finance.payment.prepare");
  const [amount, setAmount] = useState("");
  const [decision, setDecision] = useState<PolicyDecision | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError(""); setDecision(null);
    try { setDecision(await api.evaluate({ action_type: action, resource: "finance:payment", operation: "prepare", amount: amount ? Number(amount) : undefined, currency: "ZMW", supplier_verified: true })); }
    catch (e) { setError(e instanceof ApiError ? e.message : "Evaluation failed."); } finally { setLoading(false); }
  }
  return <div className="p-6"><h1 className="mb-4 text-2xl font-bold text-slate-800">Policy Simulator</h1><div className="max-w-2xl rounded-lg border bg-white p-6 shadow-sm"><p className="text-sm text-slate-500">Evaluations use the authenticated server-side policy endpoint.</p><form onSubmit={submit} className="mt-4 space-y-3"><input value={action} onChange={(e) => setAction(e.target.value)} className="w-full rounded border px-3 py-2 text-sm" placeholder="Action type" required /><input value={amount} onChange={(e) => setAmount(e.target.value)} type="number" min="0" className="w-full rounded border px-3 py-2 text-sm" placeholder="Amount (optional)" /><button disabled={loading} className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50">{loading ? "Evaluating…" : "Evaluate"}</button></form>{error && <p className="mt-4 text-sm text-red-700">Evaluation unavailable: {error}</p>}{decision && <div className="mt-5 rounded border p-4 text-sm"><p className="font-semibold">{decision.decision} · {decision.risk_level}</p><p className="mt-1">{decision.reason}</p><p className="mt-2 text-slate-500">Matched policies: {decision.matched_policies.join(", ") || "none"}</p></div>}</div></div>;
}
