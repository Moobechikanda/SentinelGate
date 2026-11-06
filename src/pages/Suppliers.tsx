import { suppliers } from "../data/mock";
export default function Suppliers() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-800 mb-4">Suppliers</h1>
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50"><tr className="text-left text-slate-500"><th className="p-3">Name</th><th>Code</th><th>Country</th><th>Bank</th><th>Account</th><th>Verification</th></tr></thead>
          <tbody>
            {suppliers.map(s=>(
              <tr key={s.id} className="border-t">
                <td className="p-3 font-medium">{s.name}</td><td>{s.code}</td><td>{s.country}</td><td>{s.bankName}</td><td>{s.accountNumber}</td>
                <td><span className={`px-2 py-0.5 rounded text-xs ${s.verification==="VERIFIED"?"bg-green-100 text-green-700":s.verification==="UNVERIFIED"?"bg-red-100 text-red-700":"bg-amber-100 text-amber-700"}`}>{s.verification}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
