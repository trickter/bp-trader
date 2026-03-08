import { CandlestickChart } from "../components/candlestick-chart";
import { LoadingBlock, SectionState } from "../components/async-state";
import { DataTable } from "../components/data-table";
import { Card } from "../components/ui/card";
import { SectionTitle } from "../components/ui/section-title";
import { useBacktestRun } from "../hooks/use-backtest-run";
import { formatCurrency } from "../lib/utils";

const DEMO_REQUEST = {
  symbol: "BTC_USDC_PERP",
  interval: "1d",
  startTime: 1740787200,
  endTime: 1741305600,
  priceSource: "last" as const,
  feeBps: 2,
  slippageBps: 4,
};

export function BacktestsPage() {
  const backtest = useBacktestRun({
    strategyId: "strat_001",
    strategyKind: "template",
    request: DEMO_REQUEST,
  });

  if (backtest.loading) {
    return (
      <div className="space-y-6">
        <section className="grid gap-4 md:grid-cols-4">
          <LoadingBlock rows={1} className="rounded-[28px]" />
          <LoadingBlock rows={1} className="rounded-[28px]" />
          <LoadingBlock rows={1} className="rounded-[28px]" />
          <LoadingBlock rows={1} className="rounded-[28px]" />
        </section>
        <LoadingBlock rows={1} className="h-96" />
      </div>
    );
  }

  if (backtest.error) {
    return (
      <SectionState
        title="Backtest lifecycle failed"
        detail={backtest.error}
        tone="error"
      />
    );
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-4">
        <Card>
          <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">Return</p>
          <p className="mt-3 text-3xl font-semibold text-white">{backtest.result.totalReturn.toFixed(2)}%</p>
        </Card>
        <Card>
          <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">Max drawdown</p>
          <p className="mt-3 text-3xl font-semibold text-white">{backtest.result.maxDrawdown.toFixed(2)}%</p>
        </Card>
        <Card>
          <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">Sharpe</p>
          <p className="mt-3 text-3xl font-semibold text-white">{backtest.result.sharpe.toFixed(2)}</p>
        </Card>
        <Card>
          <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">Lifecycle</p>
          <p className="mt-3 text-xl font-semibold text-white">{backtest.run?.status ?? backtest.result.status}</p>
          <p className="mt-2 text-sm text-slate-400">
            {backtest.run?.demoMode ? "demo-isolated request" : "provider-backed request"}
          </p>
        </Card>
      </section>

      <Card>
        <SectionTitle
          eyebrow="Backtest lifecycle"
          title={backtest.result.strategyName}
          description="The UI creates a backtest run first, then resolves the result by id using the same API contract an agent would use."
        />
        <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border border-white/8 bg-white/5 p-4 text-sm text-slate-300">
            Run id: <span className="text-white">{backtest.run?.id ?? backtest.result.id}</span>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/5 p-4 text-sm text-slate-300">
            Symbol: <span className="text-white">{backtest.result.symbol}</span>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/5 p-4 text-sm text-slate-300">
            Interval: <span className="text-white">{backtest.result.interval}</span>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/5 p-4 text-sm text-slate-300">
            Price source: <span className="text-white">{backtest.result.priceSource.toUpperCase()}</span>
          </div>
        </div>
      </Card>

      <CandlestickChart result={backtest.result} />

      <section className="grid gap-6 xl:grid-cols-[1.25fr_0.95fr]">
        <Card>
          <SectionTitle
            eyebrow="Trade markers"
            title="Open / close lifecycle"
            description="Markers are stored and rendered from normalized trade events, not reconstructed in the UI."
          />
          {backtest.result.tradeMarkers.length === 0 ? (
            <SectionState
              title="No trade markers returned"
              detail="This run completed without any entries or exits to render."
            />
          ) : (
            <DataTable
              rows={backtest.result.tradeMarkers}
              getRowKey={(item) => item.id}
              columns={[
                { key: "time", label: "Timestamp", render: (item) => item.timestamp },
                { key: "type", label: "Type", render: (item) => item.type },
                { key: "side", label: "Side", render: (item) => item.side },
                { key: "price", label: "Price", render: (item) => formatCurrency(item.price) },
                { key: "reason", label: "Reason", render: (item) => item.reason },
              ]}
            />
          )}
        </Card>
        <Card>
          <SectionTitle
            eyebrow="Execution semantics"
            title="Backtest controls"
            description="The run contract keeps creation and retrieval explicit even while the mock adapter completes immediately."
          />
          <div className="space-y-4 text-sm text-slate-300">
            <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
              Fees: {backtest.result.feeBps} bps, slippage: {backtest.result.slippageBps} bps
            </div>
            <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
              Window: {backtest.result.startTime} → {backtest.result.endTime}
            </div>
            <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
              Result path: {backtest.run?.resultPath ?? `/api/backtests/${backtest.result.id}`}
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}
