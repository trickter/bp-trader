import { Outlet, NavLink } from "react-router-dom";

import { cn } from "../lib/utils";

const navItems = [
  { to: "/profile", label: "Profile" },
  { to: "/strategies", label: "Strategy Lab" },
  { to: "/backtests", label: "Backtests" },
  { to: "/market-pulse", label: "Market Pulse" },
  { to: "/execution", label: "Execution" },
  { to: "/risk-controls", label: "Risk Controls" },
  { to: "/alerts", label: "Alerts" },
  { to: "/settings", label: "Settings" },
];

type DashboardLayoutProps = {
  onLogout: () => void;
};

export function DashboardLayout({ onLogout }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-[#020817] text-white">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top_left,rgba(56,189,248,0.18),transparent_24%),radial-gradient(circle_at_top_right,rgba(14,165,233,0.12),transparent_22%),radial-gradient(circle_at_bottom,rgba(14,165,233,0.1),transparent_28%)]" />
      <div className="relative mx-auto flex min-h-screen max-w-[1680px] gap-6 px-4 py-4 md:px-6 lg:px-8">
        <aside className="hidden w-[248px] shrink-0 rounded-[32px] border border-cyan-400/10 bg-[linear-gradient(180deg,rgba(4,17,45,0.94),rgba(4,12,28,0.98))] p-6 shadow-[0_20px_80px_rgba(0,0,0,0.45)] lg:flex lg:flex-col">
          <div className="mb-10">
            <p className="text-2xl font-semibold tracking-tight text-white">Trader Console</p>
            <p className="mt-2 text-xs uppercase tracking-[0.34em] text-cyan-200/50">
              Backpack Quant Stack
            </p>
          </div>
          <nav className="flex flex-1 flex-col gap-2">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "rounded-2xl px-4 py-3 text-sm text-slate-400 transition hover:bg-white/6 hover:text-white",
                    isActive &&
                      "bg-[linear-gradient(90deg,rgba(56,189,248,0.18),rgba(56,189,248,0.08))] text-white shadow-[inset_0_0_0_1px_rgba(56,189,248,0.2)]",
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="rounded-[24px] border border-emerald-400/10 bg-emerald-400/6 p-4">
            <p className="text-[11px] uppercase tracking-[0.28em] text-emerald-200/60">Live posture</p>
            <p className="mt-2 text-sm text-emerald-100">Execution locked to disabled/paper-ready mode.</p>
          </div>
        </aside>

        <main className="flex-1 py-2">
          <header className="mb-6 flex flex-col gap-4 rounded-[32px] border border-white/8 bg-[linear-gradient(180deg,rgba(6,17,38,0.82),rgba(5,13,28,0.88))] px-6 py-5 shadow-[0_20px_80px_rgba(0,0,0,0.4)] md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-[0.38em] text-cyan-200/50">Admin-only operating surface</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">Portfolio Matrix</h1>
              <p className="mt-2 max-w-2xl text-sm text-slate-400">
                Normalized portfolio, strategy, backtest, and risk workflows aligned around explicit
                price-source and time semantics.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={onLogout}
                className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.26em] text-slate-200 transition hover:bg-white/10"
              >
                Logout
              </button>
              <div className="rounded-full border border-emerald-400/20 bg-emerald-400/8 px-4 py-2 text-xs uppercase tracking-[0.26em] text-emerald-200">
                Live feed staged
              </div>
              <div className="grid h-11 w-11 place-items-center rounded-2xl border border-white/10 bg-white/5 text-sm text-slate-200">
                TC
              </div>
            </div>
          </header>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
