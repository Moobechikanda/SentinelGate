import { agents } from "../data/mock";
export default function Agents() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-800 mb-4">AI Agents</h1>
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50"><tr className="text-left text-slate-500"><th className="p-3">Name</th><th>Type</th><th>Environment</th><th>Status</th><th>Owner</th><th>Capabilities</th></tr></thead>
          <tbody>
            {agents.map(a => (
              <tr key={a.id} className="border-t">
                <td className="p-3 font-medium">{a.name}</td><td>{a.type}</td><td>{a.env}</td>
                <td><span className={`px-2 py-0.5 rounded text-xs ${a.status==="Active"?"bg-green-100 text-green-700":"bg-red-100 text-red-700"}`}>{a.status}</span></td>
                <td>{a.owner}</td><td className="text-xs">{a.capabilities.join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
