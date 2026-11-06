import { useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../api/client";

export default function Approvals() {
  const [id, setId] = useState(""); const [message, setMessage] = useState(""); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); setMessage(""); try { const result = await api.approvePayment(id); setMessage(`Payment ${result.id} is now ${result.status} (${result.approval_count ?? 0} approvals).`); } catch (e) { setMessage(e instanceof ApiError ? `Request failed: ${e.message}` : "Request failed."); } finally { setBusy(false); } }
  return <div className="p-6"><h1 className="mb-4 text-2xl font-bold text-slate-800">Approval Center</h1><div className="max-w-xl rounded-lg border bg-white p-5 shadow-sm"><h2 className="font-semibold">Approve a payment</h2><p className="mt-1 text-sm text-slate-500">The API does not expose approval listings. This action is authenticated and tenant-scoped by the backend.</p><form onSubmit={submit} className="mt-4 flex gap-2"><input value={id} onChange={(e) => setId(e.target.value)} className="min-w-0 flex-1 rounded border px-3 py-2 text-sm" placeholder="Payment ID" required /><button disabled={busy} className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50">{busy ? "Submitting…" : "Approve"}</button></form>{message && <p className="mt-4 text-sm text-slate-700">{message}</p>}</div></div>;
}
