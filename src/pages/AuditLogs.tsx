import { auditEvents } from "../data/mock";
export default function AuditLogs() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-800 mb-4">Audit Logs</h1>
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50"><tr className="text-left text-slate-500"><th className="p-3">Time</th><th>Actor</th><th>Type</th><th>Resource</th><th>Decision</th><th>Risk</th><th>Reason</th></tr></thead>
          <tbody>
            {auditEvents.map(e=>(
              <tr key={e.id} className="border-t">
                <td className="p-3 text-xs">{e.timestamp}</td><td>{e.actor}</td><td>{e.type}</td><td>{e.resource}</td>
                <td className={e.decision==="ALLOW"?"text-green-600":e.decision==="DENY"?"text-red-600":"text-amber-600"}>{e.decision}</td>
                <td>{e.risk}</td><td className="text-xs">{e.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
