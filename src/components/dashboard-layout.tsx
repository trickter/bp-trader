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
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <div className="relative mx-auto flex min-h-screen max-w-[1680px]">
        {/* Sidebar */}
        <aside className="hidden w-[220px] shrink-0 border-r border-gray-100 bg-white lg:flex lg:flex-col">
          <div className="border-b border-gray-100 px-5 py-5">
            <p className="font-sans text-sm font-bold tracking-tight text-gray-900">Trader Console</p>
            <p className="ui-kicker mt-0.5 text-[9px] font-semibold text-gray-400">
              Backpack Quant Stack
            </p>
          </div>

          <nav className="flex flex-1 flex-col gap-0.5 p-3">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center rounded-xl px-3 py-2.5 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-50 hover:text-gray-900",
                    isActive && "bg-gray-900 text-white hover:bg-gray-900 hover:text-white",
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="border-t border-gray-100 p-4">
            <div className="rounded-xl bg-emerald-50 px-3 py-3 ring-1 ring-emerald-100">
              <p className="ui-kicker text-[9px] font-semibold text-emerald-600">
                Live posture
              </p>
              <p className="mt-1 text-xs text-emerald-700">
                Locked to paper-ready mode.
              </p>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex min-h-screen flex-1 flex-col">
          <header className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-100 bg-white px-6 py-3.5">
            <div>
              <h1 className="font-sans text-base font-bold tracking-tight text-gray-900">Portfolio Matrix</h1>
              <p className="text-xs text-gray-400">Admin-only operating surface</p>
            </div>
            <div className="flex items-center gap-2.5">
              <div className="ui-kicker rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[9px] font-semibold text-emerald-700">
                Live feed staged
              </div>
              <div className="grid h-8 w-8 place-items-center rounded-full bg-gray-100 text-[11px] font-semibold text-gray-700">
                TC
              </div>
              <button
                type="button"
                onClick={onLogout}
                className="rounded-full border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:border-gray-900 hover:text-gray-900"
              >
                Logout
              </button>
            </div>
          </header>

          <div className="flex-1 p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
