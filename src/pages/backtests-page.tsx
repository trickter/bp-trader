import { CandlestickChart } from "../components/candlestick-chart";
import { DataTable } from "../components/data-table";
import { Card } from "../components/ui/card";
import { SectionTitle } from "../components/ui/section-title";
import { useDashboardData } from "../hooks/use-dashboard-data";
import { api } from "../lib/api";
import { formatCurrency } from "../lib/utils";

export function BacktestsPage() {
  const backtest = useDashboardData(api.backtest, {
    id: "",
    strategyName: "",
    priceSource: "mark",
    totalReturn: 0,
    maxDrawdown: 0,
    sharpe: 0,
    winRate: 0,
    candles: [],
    tradeMarkers: [],
    equityCurve: [],
  });

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-4">
        <Card>
          <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">Return</p>
          <p className="mt-3 text-3xl font-semibold text-white">{backtest.data.totalReturn.toFixed(2)}%</p>
        </Card>
        <Card>
          <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">Max drawdown</p>
          <p className="mt-3 text-3xl font-semibold text-white">{backtest.data.maxDrawdown.toFixed(2)}%</p>
        </Card>
        <Card>
          <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">Sharpe</p>
          <p className="mt-3 text-3xl font-semibold text-white">{backtest.data.sharpe.toFixed(2)}</p>
        </Card>
        <Card>
          <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">Price source</p>
          <p className="mt-3 text-3xl font-semibold text-white">{backtest.data.priceSource.toUpperCase()}</p>
        </Card>
      </section>

      <CandlestickChart result={backtest.data} />

      <section className="grid gap-6 xl:grid-cols-[1.25fr_0.95fr]">
        <Card>
          <SectionTitle
            eyebrow="Trade markers"
            title="Open / close lifecycle"
            description="Markers are stored and rendered from normalized trade events, not reconstructed in the UI."
          />
          <DataTable
            rows={backtest.data.tradeMarkers}
            columns={[
              { key: "time", label: "Timestamp", render: (item) => item.timestamp },
              { key: "type", label: "Type", render: (item) => item.type },
              { key: "side", label: "Side", render: (item) => item.side },
              { key: "price", label: "Price", render: (item) => formatCurrency(item.price) },
              { key: "reason", label: "Reason", render: (item) => item.reason },
            ]}
          />
        </Card>
        <Card>
          <SectionTitle
            eyebrow="Execution semantics"
            title="Backtest controls"
            description="The first version is K-line driven with explicit price-source selection."
          />
          <div className="space-y-4 text-sm text-slate-300">
            <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
              Interval: `1h`
            </div>
            <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
              Fees and slippage modeled inside event loop
            </div>
            <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
              Funding settlement accounted as account events
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}
