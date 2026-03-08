import { DataTable } from "../components/data-table";
import { StatCard } from "../components/stat-card";
import { Card } from "../components/ui/card";
import { SectionTitle } from "../components/ui/section-title";
import { StatusPill } from "../components/ui/status-pill";
import { useDashboardData } from "../hooks/use-dashboard-data";
import { api } from "../lib/api";
import { formatCurrency, formatPercent } from "../lib/utils";

export function ProfilePage() {
  const summary = useDashboardData(api.profileSummary, {
    totalEquity: 0,
    availableMargin: 0,
    unrealizedPnl: 0,
    realizedPnl24h: 0,
    winRate: 0,
    riskLevel: "Waiting",
    priceSource: "mark",
    syncedAt: "",
  });
  const assets = useDashboardData(api.profileAssets, []);
  const positions = useDashboardData(api.profilePositions, []);
  const events = useDashboardData(api.accountEvents, []);

  return (
    <div className="space-y-6">
      <section className="grid gap-4 xl:grid-cols-4">
        <StatCard
          label="Total equity"
          value={formatCurrency(summary.data.totalEquity)}
          helper={`Available margin ${formatCurrency(summary.data.availableMargin)}`}
          badge="Portfolio"
        />
        <StatCard
          label="Unrealized pnl"
          value={formatCurrency(summary.data.unrealizedPnl)}
          helper={`Price source ${summary.data.priceSource.toUpperCase()}`}
          badge={summary.data.unrealizedPnl >= 0 ? "Expanding" : "Compressing"}
          tone={summary.data.unrealizedPnl >= 0 ? "positive" : "negative"}
        />
        <StatCard
          label="24h realized"
          value={formatCurrency(summary.data.realizedPnl24h)}
          helper={`Risk posture ${summary.data.riskLevel}`}
          badge="Session"
          tone="positive"
        />
        <StatCard
          label="Win rate"
          value={`${summary.data.winRate.toFixed(1)}%`}
          helper={`Synced ${summary.data.syncedAt || "pending"}`}
          badge="Observed"
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.05fr_1.35fr]">
        <Card>
          <SectionTitle
            eyebrow="Profile"
            title="Asset balances"
            description="Collateral-aware inventory with explicit contribution to total equity."
          />
          <DataTable
            rows={assets.data}
            columns={[
              { key: "asset", label: "Asset", render: (item) => item.asset },
              { key: "available", label: "Available", render: (item) => item.available.toLocaleString() },
              { key: "locked", label: "Locked", render: (item) => item.locked.toLocaleString() },
              {
                key: "value",
                label: "Collateral value",
                render: (item) => formatCurrency(item.collateralValue),
              },
              {
                key: "weight",
                label: "Weight",
                render: (item) => formatPercent(item.portfolioWeight),
              },
            ]}
          />
        </Card>

        <Card>
          <SectionTitle
            eyebrow="Profile"
            title="Open positions"
            description="Normalized positions insulated from exchange field drift."
          />
          <DataTable
            rows={positions.data}
            columns={[
              { key: "symbol", label: "Symbol", render: (item) => item.symbol },
              {
                key: "side",
                label: "Side",
                render: (item) => (
                  <StatusPill tone={item.side === "long" ? "positive" : "negative"}>
                    {item.side}
                  </StatusPill>
                ),
              },
              { key: "qty", label: "Qty", render: (item) => item.quantity.toFixed(3) },
              { key: "entry", label: "Entry", render: (item) => formatCurrency(item.entryPrice) },
              { key: "mark", label: "Mark", render: (item) => formatCurrency(item.markPrice) },
              { key: "pnl", label: "PnL", render: (item) => formatCurrency(item.unrealizedPnl) },
              { key: "margin", label: "Margin", render: (item) => formatCurrency(item.marginUsed) },
            ]}
          />
        </Card>
      </section>

      <Card>
        <SectionTitle
          eyebrow="Account events"
          title="Ledger timeline"
          description="Funding, fees, fills, and system-origin events stay separated for attribution."
        />
        <DataTable
          rows={events.data}
          columns={[
            { key: "type", label: "Event type", render: (item) => item.eventType },
            { key: "origin", label: "Origin", render: (item) => item.eventOrigin },
            { key: "asset", label: "Asset", render: (item) => item.asset },
            { key: "amount", label: "Amount", render: (item) => item.amount.toLocaleString() },
            { key: "pnl", label: "PnL effect", render: (item) => formatCurrency(item.pnlEffect) },
            { key: "position", label: "Position effect", render: (item) => item.positionEffect },
            { key: "time", label: "Occurred", render: (item) => item.occurredAt },
          ]}
        />
      </Card>
    </div>
  );
}
