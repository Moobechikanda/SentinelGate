import { policies } from "../data/mock";
export default function Policies() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-800 mb-4">Policy Center</h1>
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50"><tr className="text-left text-slate-500"><th className="p-3">Name</th><th>Category</th><th>Decision</th><th>Status</th><th>Version</th></tr></thead>
          <tbody>
            {policies.map(p=>(
              <tr key={p.id} className="border-t">
                <td className="p-3 font-medium">{p.name}</td><td>{p.category}</td>
                <td className={p.decision==="ALLOW"?"text-green-600":p.decision==="DENY"?"text-red-600":"text-amber-600"}>{p.decision}</td>
                <td>{p.status}</td><td>v{p.version}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
