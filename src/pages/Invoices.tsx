import { invoices, suppliers } from "../data/mock";
export default function Invoices() {
  const name = (id: string) => suppliers.find(s=>s.id===id)?.name ?? id;
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-800 mb-4">Invoices</h1>
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50"><tr className="text-left text-slate-500"><th className="p-3">Number</th><th>Supplier</th><th>Amount</th><th>Date</th><th>Due</th><th>Status</th></tr></thead>
          <tbody>
            {invoices.map(i=>(
              <tr key={i.id} className="border-t">
                <td className="p-3">{i.number}</td><td>{name(i.supplierId)}</td><td>{i.amount.toLocaleString()} {i.currency}</td><td>{i.date}</td><td>{i.dueDate}</td><td>{i.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
