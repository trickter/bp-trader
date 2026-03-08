import { DataTable } from "../components/data-table";
import { Card } from "../components/ui/card";
import { SectionTitle } from "../components/ui/section-title";
import { StatusPill } from "../components/ui/status-pill";
import { useDashboardData } from "../hooks/use-dashboard-data";
import { api } from "../lib/api";

export function StrategiesPage() {
  const strategies = useDashboardData(api.strategies, []);

  return (
    <div className="grid gap-6 xl:grid-cols-[1.5fr_0.9fr]">
      <Card>
        <SectionTitle
          eyebrow="Strategy stack"
          title="Strategy registry"
          description="Templates and script-based strategies compile into the same normalized execution intent."
        />
        <DataTable
          rows={strategies.data}
          columns={[
            { key: "name", label: "Strategy", render: (item) => item.name },
            { key: "kind", label: "Kind", render: (item) => item.kind },
            { key: "market", label: "Market", render: (item) => item.market },
            {
              key: "runtime",
              label: "Runtime",
              render: (item) => <StatusPill>{item.runtime}</StatusPill>,
            },
            {
              key: "status",
              label: "Status",
              render: (item) => (
                <StatusPill tone={item.status === "healthy" ? "positive" : "neutral"}>
                  {item.status}
                </StatusPill>
              ),
            },
            { key: "sharpe", label: "Sharpe", render: (item) => item.sharpe.toFixed(2) },
            { key: "priceSource", label: "Price source", render: (item) => item.priceSource },
          ]}
        />
      </Card>

      <div className="space-y-6">
        <Card>
          <SectionTitle
            eyebrow="Template lanes"
            title="Fast-start kits"
            description="EMA crossover, breakout, mean-reversion, and funding-bias recipes are parameter-driven."
          />
          <div className="grid gap-3 text-sm text-slate-300">
            {[
              "EMA Trend Stack",
              "ATR Breakout Window",
              "Volatility Compression",
              "Funding Dislocation",
            ].map((name) => (
              <div key={name} className="rounded-2xl border border-white/8 bg-white/5 px-4 py-3">
                {name}
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <SectionTitle
            eyebrow="Script policy"
            title="Sandbox envelope"
            description="No egress, no arbitrary packages, fixed runtime profile, deterministic seeds."
          />
          <ul className="space-y-3 text-sm text-slate-300">
            <li>Python worker with white-listed libraries only.</li>
            <li>Resource-limited backtests with saved code hash and dependency profile.</li>
            <li>Signals and intents must match normalized schemas before execution staging.</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
