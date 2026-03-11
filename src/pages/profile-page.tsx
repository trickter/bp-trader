import { LoadingBlock, MetricSkeletonGrid, SectionState } from "../components/async-state";
import { DataTable } from "../components/data-table";
import { StatCard } from "../components/stat-card";
import { Card } from "../components/ui/card";
import { SectionTitle } from "../components/ui/section-title";
import { StatusPill } from "../components/ui/status-pill";
import { useDashboardData } from "../hooks/use-dashboard-data";
import { api } from "../lib/api";
import { formatCurrency, formatPercent } from "../lib/utils";

export function ProfilePage() {
  const summaryFallback = {
    totalEquity: 0,
    availableMargin: 0,
    unrealizedPnl: 0,
    realizedPnl24h: 0,
    winRate: 0,
    riskLevel: "Waiting",
    priceSource: "mark" as const,
    syncedAt: "",
  };
  const summary = useDashboardData(api.profileSummary, {
    ...summaryFallback,
  });
  const assets = useDashboardData(api.profileAssets, []);
  const positions = useDashboardData(api.profilePositions, []);
  const events = useDashboardData(api.accountEvents, []);
  const profileError = summary.error ?? assets.error ?? positions.error ?? events.error;

  return (
    <div className="space-y-6">
      {summary.loading ? (
        <MetricSkeletonGrid />
      ) : summary.error ? (
        <SectionState
          title="Profile summary unavailable"
          detail={summary.error}
          tone="error"
        />
      ) : (
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
      )}

      {profileError ? (
        <SectionState
          title="Profile data is degraded"
          detail={`One or more portfolio feeds failed: ${profileError}`}
          tone="error"
        />
      ) : null}

      <section className="grid gap-6 xl:grid-cols-[1.05fr_1.35fr]">
        <Card>
          <SectionTitle
            eyebrow="Profile"
            title="Asset balances"
            description="Collateral-aware inventory with explicit contribution to total equity."
          />
          {assets.loading ? (
            <LoadingBlock />
          ) : assets.error ? (
            <SectionState
              title="Asset balances failed to load"
              detail={assets.error}
              tone="error"
            />
          ) : assets.data.length === 0 ? (
            <SectionState
              title="No asset balances yet"
              detail="Connect a funded account or wait for the next snapshot sync."
            />
          ) : (
            <DataTable
              rows={assets.data}
              getRowKey={(item) => item.asset}
              columns={[
                { key: "asset", label: "Asset", render: (item) => item.asset },
                {
                  key: "available",
                  label: "Available",
                  render: (item) => <span className="financial-data">{item.available.toLocaleString()}</span>,
                },
                {
                  key: "locked",
                  label: "Locked",
                  render: (item) => <span className="financial-data">{item.locked.toLocaleString()}</span>,
                },
                {
                  key: "value",
                  label: "Collateral value",
                  render: (item) => <span className="financial-data">{formatCurrency(item.collateralValue)}</span>,
                },
                {
                  key: "weight",
                  label: "Weight",
                  render: (item) => <span className="financial-data">{formatPercent(item.portfolioWeight)}</span>,
                },
              ]}
            />
          )}
        </Card>

        <Card>
          <SectionTitle
            eyebrow="Profile"
            title="Open positions"
            description="Normalized positions insulated from exchange field drift."
          />
          {positions.loading ? (
            <LoadingBlock />
          ) : positions.error ? (
            <SectionState
              title="Positions failed to load"
              detail={positions.error}
              tone="error"
            />
          ) : positions.data.length === 0 ? (
            <SectionState
              title="No open positions"
              detail="The account is flat. New positions will appear here with normalized pricing fields."
            />
          ) : (
            <DataTable
              rows={positions.data}
              getRowKey={(item) => `${item.symbol}-${item.side}-${item.openedAt}`}
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
                { key: "qty", label: "Qty", render: (item) => <span className="financial-data">{item.quantity.toFixed(3)}</span> },
                { key: "entry", label: "Entry", render: (item) => <span className="financial-data">{formatCurrency(item.entryPrice)}</span> },
                { key: "mark", label: "Mark", render: (item) => <span className="financial-data">{formatCurrency(item.markPrice)}</span> },
                { key: "pnl", label: "PnL", render: (item) => <span className="financial-data">{formatCurrency(item.unrealizedPnl)}</span> },
                { key: "margin", label: "Margin", render: (item) => <span className="financial-data">{formatCurrency(item.marginUsed)}</span> },
              ]}
            />
          )}
        </Card>
      </section>

      <Card>
        <SectionTitle
          eyebrow="Account events"
          title="Ledger timeline"
          description="Funding, fees, fills, and system-origin events stay separated for attribution."
        />
        {events.loading ? (
          <LoadingBlock rows={4} />
        ) : events.error ? (
          <SectionState
            title="Ledger timeline failed to load"
            detail={events.error}
            tone="error"
          />
        ) : events.data.length === 0 ? (
          <SectionState
            title="No account events yet"
            detail="Funding, fees, fills, and system events will be appended once activity is detected."
          />
        ) : (
          <DataTable
            rows={events.data}
            getRowKey={(item) => item.id}
            columns={[
              { key: "type", label: "Event type", render: (item) => item.eventType },
              { key: "origin", label: "Origin", render: (item) => item.origin },
              { key: "asset", label: "Asset", render: (item) => item.asset },
              { key: "amount", label: "Amount", render: (item) => <span className="financial-data">{item.amount.toLocaleString()}</span> },
              { key: "pnl", label: "PnL effect", render: (item) => <span className="financial-data">{formatCurrency(item.pnlEffect)}</span> },
              { key: "position", label: "Position effect", render: (item) => item.positionEffect },
              { key: "time", label: "Occurred", render: (item) => <span className="financial-data text-xs">{item.occurredAt}</span> },
            ]}
          />
        )}
      </Card>
    </div>
  );
}
