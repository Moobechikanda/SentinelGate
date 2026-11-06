import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { LayoutDashboard, Shield, DollarSign, FileText, Users, ScrollText, Settings, ChevronLeft } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError, tokenStorage } from "./api/client";
import Dashboard from "./pages/Dashboard";
import Agents from "./pages/Agents";
import Tools from "./pages/Tools";
import AgentActivity from "./pages/AgentActivity";
import SecurityEvents from "./pages/SecurityEvents";
import Transactions from "./pages/Transactions";
import Suppliers from "./pages/Suppliers";
import Invoices from "./pages/Invoices";
import Approvals from "./pages/Approvals";
import Policies from "./pages/Policies";
import PolicySimulator from "./pages/PolicySimulator";
import AuditLogs from "./pages/AuditLogs";
import Reports from "./pages/Reports";
import SettingsPage from "./pages/SettingsPage";
import Integrations from "./pages/Integrations";

const nav = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/agents", label: "Agents", icon: Shield },
  { to: "/tools", label: "Connected Tools", icon: Shield },
  { to: "/agent-activity", label: "Agent Activity", icon: ScrollText },
  { to: "/security-events", label: "Security Events", icon: Shield },
  { to: "/transactions", label: "Transactions", icon: DollarSign },
  { to: "/suppliers", label: "Suppliers", icon: Users },
  { to: "/invoices", label: "Invoices", icon: FileText },
  { to: "/approvals", label: "Approvals", icon: Shield },
  { to: "/policies", label: "Policies", icon: Shield },
  { to: "/policy-simulator", label: "Policy Simulator", icon: Shield },
  { to: "/audit", label: "Audit Logs", icon: ScrollText },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/integrations", label: "Integrations", icon: Shield },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [token, setToken] = useState(tokenStorage.get());
  const [bootstrapToken, setBootstrapToken] = useState("dev-bootstrap-token");
  const [loginError, setLoginError] = useState("");
  const [loggingIn, setLoggingIn] = useState(false);

  async function login(event: FormEvent) {
    event.preventDefault();
    setLoggingIn(true);
    setLoginError("");
    tokenStorage.set(bootstrapToken.trim());
    try {
      await api.getAudit();
      setToken(bootstrapToken.trim());
    } catch (error) {
      tokenStorage.clear();
      setLoginError(error instanceof ApiError ? error.message : "Login failed.");
    } finally {
      setLoggingIn(false);
    }
  }

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
        <form onSubmit={login} className="w-full max-w-md rounded-lg border bg-white p-6 shadow-sm">
          <h1 className="text-2xl font-bold text-slate-800">SentinelGate</h1>
          <p className="mt-2 text-sm text-slate-600">Development bootstrap login. Tokens are accepted only by the non-production backend flow.</p>
          <label className="mt-5 block text-sm font-medium text-slate-700">Bootstrap token
            <input value={bootstrapToken} onChange={(e) => setBootstrapToken(e.target.value)} className="mt-1 w-full rounded border px-3 py-2" required />
          </label>
          {loginError && <p className="mt-3 text-sm text-red-700">{loginError}</p>}
          <button disabled={loggingIn} className="mt-5 rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50">{loggingIn ? "Connecting…" : "Sign in"}</button>
        </form>
      </div>
    );
  }
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-slate-50">
        <aside className={`${collapsed ? "w-16" : "w-64"} bg-slate-900 text-white transition-all flex flex-col`}>
          <div className="p-4 flex items-center justify-between border-b border-slate-700">
            {!collapsed && <span className="font-bold text-lg">SentinelGate</span>}
            <button onClick={() => setCollapsed(!collapsed)} className="text-slate-300 hover:text-white">
              <ChevronLeft className={`w-5 h-5 transition ${collapsed ? "rotate-180" : ""}`} />
            </button>
          </div>
          <nav className="flex-1 overflow-y-auto p-2 space-y-1">
            {nav.map((n) => (
              <NavLink key={n.to} to={n.to} end={n.to === "/"}
                className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-md text-sm ${isActive ? "bg-slate-700 text-white" : "text-slate-300 hover:bg-slate-800"}`}>
                <n.icon className="w-4 h-4 shrink-0" />
                {!collapsed && <span>{n.label}</span>}
              </NavLink>
            ))}
          </nav>
        </aside>
        <main className="flex-1 overflow-y-auto">
          <div className="flex justify-end border-b bg-white px-6 py-2"><button className="text-xs text-slate-600 underline" onClick={() => { tokenStorage.clear(); setToken(null); }}>Sign out</button></div>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/tools" element={<Tools />} />
            <Route path="/agent-activity" element={<AgentActivity />} />
            <Route path="/security-events" element={<SecurityEvents />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/suppliers" element={<Suppliers />} />
            <Route path="/invoices" element={<Invoices />} />
            <Route path="/approvals" element={<Approvals />} />
            <Route path="/policies" element={<Policies />} />
            <Route path="/policy-simulator" element={<PolicySimulator />} />
            <Route path="/audit" element={<AuditLogs />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/integrations" element={<Integrations />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
