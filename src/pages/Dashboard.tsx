import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { AuditEventResponse } from "../api/client";
import { ErrorState, LoadingState } from "../components/ApiState";

export default function Dashboard() {
  const [events, setEvents] = useState<AuditEventResponse[] | null>(null);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setError("");
    try { setEvents(await api.getAudit()); } catch (e) { setError(e instanceof ApiError ? e.message : "Request failed."); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  if (error) return <div className="p-6"><h1 className="mb-4 text-2xl font-bold text-slate-800">Overview</h1><ErrorState message={error} onRetry={() => void load()} /></div>;
  if (!events) return <div className="p-6"><LoadingState /></div>;
  const denied = events.filter((e) => e.details === "DENY").length;
  const allowed = events.filter((e) => e.details === "ALLOW").length;
  return <div className="space-y-6 p-6">
    <h1 className="text-2xl font-bold text-slate-800">Overview</h1>
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {[["Audit events", events.length], ["Blocked actions", denied], ["Allowed actions", allowed], ["API status", "Connected"]].map(([label, value]) => <div key={String(label)} className="rounded-lg border bg-white p-4 shadow-sm"><div className="text-xs text-slate-500">{label}</div><div className="mt-1 text-2xl font-bold text-slate-800">{value}</div></div>)}
    </div>
    <div className="rounded-lg border bg-white p-4 shadow-sm"><h2 className="mb-3 font-semibold">Recent activity</h2>
      {events.length === 0 ? <p className="text-sm text-slate-500">No audit events have been recorded.</p> : <ul className="space-y-2 text-sm">{events.slice(0, 5).map((e) => <li key={e.id} className="flex justify-between border-b pb-1"><span>{e.event_type} · {e.details}</span><span className="text-slate-500">{new Date(e.created_at).toLocaleString()}</span></li>)}</ul>}
    </div>
    <p className="text-xs text-slate-500">Transaction totals are not displayed because the current API does not expose a payment listing endpoint.</p>
  </div>;
}
