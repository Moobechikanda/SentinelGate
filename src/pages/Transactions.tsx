import { useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../api/client";

export default function Transactions() {
  const [id, setId] = useState(""); const [amount, setAmount] = useState(""); const [message, setMessage] = useState(""); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); setMessage(""); try { const result = await api.createPayment({ id, amount: Number(amount), currency: "ZMW", supplier_verified: true }); setMessage(`Payment ${result.id} created with status ${result.status}.`); } catch (e) { setMessage(e instanceof ApiError ? `Request failed: ${e.message}` : "Request failed."); } finally { setBusy(false); } }
  return <div className="p-6"><h1 className="mb-4 text-2xl font-bold text-slate-800">Transactions</h1><div className="max-w-xl rounded-lg border bg-white p-5 shadow-sm"><h2 className="font-semibold">Create simulated payment</h2><p className="mt-1 text-sm text-slate-500">The API does not expose a payment listing endpoint. This form uses the authenticated create-payment endpoint.</p><form onSubmit={submit} className="mt-4 space-y-3"><input value={id} onChange={(e) => setId(e.target.value)} className="w-full rounded border px-3 py-2 text-sm" placeholder="Payment ID" required /><input value={amount} onChange={(e) => setAmount(e.target.value)} type="number" min="0.01" step="0.01" className="w-full rounded border px-3 py-2 text-sm" placeholder="Amount (ZMW)" required /><button disabled={busy} className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50">{busy ? "Submitting…" : "Create payment"}</button></form>{message && <p className="mt-4 text-sm text-slate-700">{message}</p>}</div></div>;
}
