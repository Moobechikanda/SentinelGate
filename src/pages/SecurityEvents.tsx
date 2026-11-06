import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { AuditEventResponse } from "../api/client";
import { ErrorState, LoadingState } from "../components/ApiState";

export default function SecurityEvents() {
  const [events, setEvents] = useState<AuditEventResponse[] | null>(null);
  const [error, setError] = useState("");
  const load = useCallback(async () => { try { setError(""); setEvents(await api.getAudit()); } catch (e) { setError(e instanceof ApiError ? e.message : "Request failed."); } }, []);
  useEffect(() => { void load(); }, [load]);
  return <div className="p-6"><h1 className="mb-4 text-2xl font-bold text-slate-800">Security Events</h1>
    {error ? <ErrorState message={error} onRetry={() => void load()} /> : !events ? <LoadingState /> : <div className="overflow-hidden rounded-lg border bg-white shadow-sm"><table className="w-full text-sm"><thead className="bg-slate-50"><tr className="text-left text-slate-500"><th className="p-3">Time</th><th>Actor</th><th>Type</th><th>Details</th></tr></thead><tbody>{events.map((e) => <tr key={e.id} className="border-t"><td className="p-3 text-xs">{new Date(e.created_at).toLocaleString()}</td><td>{e.actor_id}</td><td>{e.event_type}</td><td className={e.details === "DENY" ? "text-red-600" : "text-slate-700"}>{e.details}</td></tr>)}</tbody></table>{events.length === 0 && <p className="p-4 text-sm text-slate-500">No security events have been recorded.</p>}</div>}
  </div>;
}
