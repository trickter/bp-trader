import { useEffect, useState } from "react";

import { CandlestickChart } from "../components/candlestick-chart";
import { LoadingBlock, SectionState } from "../components/async-state";
import { DataTable } from "../components/data-table";
import { Card } from "../components/ui/card";
import { SectionTitle } from "../components/ui/section-title";
import { useBacktestRun } from "../hooks/use-backtest-run";
import { api } from "../lib/api";
import type { BacktestRequest, StrategySummary } from "../lib/types";
import { formatCurrency, formatUnixDateTime, fromDatetimeLocalValue, toDatetimeLocalValue } from "../lib/utils";

const fieldClassName =
  "w-full appearance-none rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40";

const DEFAULT_END_TIME = Math.floor(Date.now() / 1000);
const DEFAULT_START_TIME = DEFAULT_END_TIME - 7 * 24 * 60 * 60;

export function BacktestsPage() {
  const [strategies, setStrategies] = useState<StrategySummary[]>([]);
  const [symbols, setSymbols] = useState<string[]>([]);
  const [selectedStrategyId, setSelectedStrategyId] = useState("");
  const [request, setRequest] = useState<BacktestRequest>({
    symbol: "BTC_USDC_PERP",
    interval: "1d",
    startTime: DEFAULT_START_TIME,
    endTime: DEFAULT_END_TIME,
    priceSource: "last",
    feeBps: 2,
    slippageBps: 4,
  });
  const [loadingSetup, setLoadingSetup] = useState(true);
  const [setupError, setSetupError] = useState<string | null>(null);
  const backtest = useBacktestRun({});

  useEffect(() => {
    let active = true;

    async function load() {
      setLoadingSetup(true);
      setSetupError(null);

      try {
        const [strategyRows, symbolRows] = await Promise.all([api.strategies(), api.marketSymbols()]);
        if (!active) {
          return;
        }
        setStrategies(strategyRows);
        setSymbols(symbolRows);
        const initial = strategyRows[0];
        if (initial) {
          setSelectedStrategyId(initial.id);
          setRequest((current) => ({
            ...current,
            symbol: initial.market,
            priceSource: initial.priceSource,
          }));
        } else if (symbolRows[0]) {
          setRequest((current) => ({ ...current, symbol: symbolRows[0] }));
        }
      } catch (cause: unknown) {
        if (!active) {
          return;
        }
        setSetupError(cause instanceof Error ? cause.message : "Unknown error");
      } finally {
        if (active) {
          setLoadingSetup(false);
        }
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  const selectedStrategy = strategies.find((item) => item.id === selectedStrategyId) ?? null;
  const formattedRunWindow = backtest.hasResult
    ? `${formatUnixDateTime(backtest.result.startTime)} UTC -> ${formatUnixDateTime(backtest.result.endTime)} UTC`
    : null;

  function handleStrategyChange(strategyId: string) {
    setSelectedStrategyId(strategyId);
    const strategy = strategies.find((item) => item.id === strategyId);
    if (!strategy) {
      return;
    }
    setRequest((current) => ({
      ...current,
      symbol: strategy.market,
      priceSource: strategy.priceSource,
    }));
  }

  async function handleRun() {
    if (!selectedStrategy) {
      return;
    }

    await backtest.runBacktest({
      strategyId: selectedStrategy.id,
      strategyKind: selectedStrategy.kind,
      request,
    });
  }

  if (loadingSetup) {
    return (
      <div className="space-y-6">
        <LoadingBlock rows={1} className="h-64" />
        <LoadingBlock rows={1} className="h-96" />
      </div>
    );
  }

  if (setupError) {
    return <SectionState title="Backtest controls failed to load" detail={setupError} tone="error" />;
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Card>
          <SectionTitle
            eyebrow="Run configuration"
            title="Create a backtest"
            description="Pick a strategy, choose the market and time window, then run the explicit POST create -> GET result flow."
          />
          <div className="grid gap-4">
            <label className="grid gap-2 text-sm text-slate-300">
              <span>Strategy</span>
              <select
                className={fieldClassName}
                style={{ colorScheme: "dark" }}
                value={selectedStrategyId}
                onChange={(event) => handleStrategyChange(event.target.value)}
              >
                {strategies.map((strategy) => (
                  <option className="bg-slate-950 text-slate-100" key={strategy.id} value={strategy.id}>
                    {strategy.name} ({strategy.kind})
                  </option>
                ))}
              </select>
            </label>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="grid gap-2 text-sm text-slate-300">
                <span>Symbol</span>
                <select
                  className={fieldClassName}
                  style={{ colorScheme: "dark" }}
                  value={request.symbol}
                  onChange={(event) => setRequest((current) => ({ ...current, symbol: event.target.value }))}
                >
                  {symbols.map((symbol) => (
                    <option className="bg-slate-950 text-slate-100" key={symbol} value={symbol}>
                      {symbol}
                    </option>
                  ))}
                </select>
              </label>
              <label className="grid gap-2 text-sm text-slate-300">
                <span>Interval</span>
                <select
                  className={fieldClassName}
                  style={{ colorScheme: "dark" }}
                  value={request.interval}
                  onChange={(event) => setRequest((current) => ({ ...current, interval: event.target.value }))}
                >
                  <option className="bg-slate-950 text-slate-100" value="15m">15m</option>
                  <option className="bg-slate-950 text-slate-100" value="1h">1h</option>
                  <option className="bg-slate-950 text-slate-100" value="4h">4h</option>
                  <option className="bg-slate-950 text-slate-100" value="1d">1d</option>
                </select>
              </label>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="grid gap-2 text-sm text-slate-300">
                <span>Start</span>
                <input
                  className={fieldClassName}
                  type="datetime-local"
                  value={toDatetimeLocalValue(request.startTime)}
                  onChange={(event) =>
                    setRequest((current) => ({ ...current, startTime: fromDatetimeLocalValue(event.target.value) }))
                  }
                />
              </label>
              <label className="grid gap-2 text-sm text-slate-300">
                <span>End</span>
                <input
                  className={fieldClassName}
                  type="datetime-local"
                  value={toDatetimeLocalValue(request.endTime)}
                  onChange={(event) =>
                    setRequest((current) => ({ ...current, endTime: fromDatetimeLocalValue(event.target.value) }))
                  }
                />
              </label>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <label className="grid gap-2 text-sm text-slate-300">
                <span>Price source</span>
                <select
                  className={fieldClassName}
                  style={{ colorScheme: "dark" }}
                  value={request.priceSource}
                  onChange={(event) =>
                    setRequest((current) => ({
                      ...current,
                      priceSource: event.target.value as BacktestRequest["priceSource"],
                    }))
                  }
                >
                  <option className="bg-slate-950 text-slate-100" value="last">last</option>
                  <option className="bg-slate-950 text-slate-100" value="mark">mark</option>
                  <option className="bg-slate-950 text-slate-100" value="index">index</option>
                </select>
              </label>
              <label className="grid gap-2 text-sm text-slate-300">
                <span>Fee (bps)</span>
                <input
                  className={fieldClassName}
                  type="number"
                  min="0"
                  value={request.feeBps}
                  onChange={(event) => setRequest((current) => ({ ...current, feeBps: Number(event.target.value) }))}
                />
              </label>
              <label className="grid gap-2 text-sm text-slate-300">
                <span>Slippage (bps)</span>
                <input
                  className={fieldClassName}
                  type="number"
                  min="0"
                  value={request.slippageBps}
                  onChange={(event) =>
                    setRequest((current) => ({ ...current, slippageBps: Number(event.target.value) }))
                  }
                />
              </label>
            </div>
            <button
              type="button"
              onClick={handleRun}
              disabled={!selectedStrategy || backtest.loading}
              className="rounded-full bg-cyan-300 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {backtest.loading ? "Running backtest..." : "Run backtest"}
            </button>
          </div>
        </Card>

        <Card>
          <SectionTitle
            eyebrow="Strategy context"
            title={selectedStrategy?.name ?? "No strategy selected"}
            description="Use this side panel as the run brief: metadata, parameter snapshot, and execution lane before you launch a backtest."
          />
          {selectedStrategy ? (
            <div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-1">
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4 text-sm text-slate-300">
                  Kind: <span className="text-white">{selectedStrategy.kind}</span>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4 text-sm text-slate-300">
                  Runtime: <span className="text-white">{selectedStrategy.runtime}</span>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4 text-sm text-slate-300">
                  Default market: <span className="text-white">{selectedStrategy.market}</span>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4 text-sm text-slate-300">
                  Price source: <span className="text-white">{selectedStrategy.priceSource.toUpperCase()}</span>
                </div>
              </div>
              <div className="rounded-[24px] border border-cyan-400/10 bg-[linear-gradient(180deg,rgba(34,211,238,0.08),rgba(15,23,42,0.35))] p-4">
                <p className="text-[11px] uppercase tracking-[0.28em] text-cyan-100/60">Parameter snapshot</p>
                <pre className="mt-3 overflow-x-auto text-xs leading-6 text-slate-200">
                  {JSON.stringify(selectedStrategy.parameters, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <SectionState title="No strategy selected" detail="Choose a strategy from the left to inspect its metadata." />
          )}
        </Card>
      </section>

      {backtest.error ? (
        <SectionState title="Backtest lifecycle failed" detail={backtest.error} tone="error" />
      ) : null}

      {!backtest.hasResult ? (
        <SectionState
          title="No backtest run yet"
          detail="Fill the controls above and start a run. Results, chart markers, and lifecycle metadata will appear here."
        />
      ) : (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
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
            <Card>
              <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">Trade count</p>
              <p className="mt-3 text-3xl font-semibold text-white">{backtest.result.tradeMarkers.length}</p>
              <p className="mt-2 text-sm text-slate-400">Lifecycle markers in current run</p>
            </Card>
          </section>

          <section className="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
            <CandlestickChart result={backtest.result} />

            <Card>
              <SectionTitle
                eyebrow="Run brief"
                title={backtest.result.strategyName}
                description="This panel keeps the backtest envelope explicit while the chart stays dedicated to price and execution analysis."
              />
              <div className="space-y-4 text-sm text-slate-300">
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  Run id: <span className="text-white">{backtest.run?.id ?? backtest.result.id}</span>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  Symbol: <span className="text-white">{backtest.result.symbol}</span>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  Interval: <span className="text-white">{backtest.result.interval}</span>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  Price source: <span className="text-white">{backtest.result.priceSource.toUpperCase()}</span>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  Exchange: <span className="text-white">{backtest.result.exchangeId || "unknown"}</span> /{" "}
                  <span className="text-white">{backtest.result.marketType || "unknown"}</span>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  Window: <span className="text-white">{formattedRunWindow}</span>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  Result path: <span className="text-white break-all">{backtest.run?.resultPath ?? `/api/backtests/${backtest.result.id}`}</span>
                </div>
              </div>
            </Card>
          </section>

          <section className="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
            <Card>
              <SectionTitle
                eyebrow="Trade markers"
                title="Open / close lifecycle"
                description="Markers are stored and rendered from normalized trade events, not reconstructed in the UI."
              />
              {backtest.result.tradeMarkers.length === 0 ? (
                <SectionState title="No trade markers returned" detail="This run completed without any entries or exits to render." />
              ) : (
                <DataTable
                  rows={backtest.result.tradeMarkers}
                  getRowKey={(item) => item.id}
                  columns={[
                    { key: "time", label: "Timestamp", render: (item) => item.timestamp },
                    { key: "action", label: "Action", render: (item) => item.action },
                    { key: "side", label: "Side", render: (item) => item.side },
                    { key: "qty", label: "Qty", render: (item) => item.qty },
                    { key: "price", label: "Price", render: (item) => formatCurrency(item.price) },
                    { key: "reason", label: "Reason", render: (item) => item.reason },
                  ]}
                />
              )}
            </Card>
            <Card>
              <SectionTitle
                eyebrow="Execution semantics"
                title="Run controls"
                description="Fees, slippage, and window settings remain visible after the run so analysis stays reproducible."
              />
              <div className="space-y-4 text-sm text-slate-300">
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  Fees: {backtest.result.feeBps} bps, slippage: {backtest.result.slippageBps} bps
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  Window: {formattedRunWindow}
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  Markers: {backtest.result.tradeMarkers.length} · Win rate: {backtest.result.winRate.toFixed(1)}%
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  Current request: {request.symbol} / {request.interval} / {request.priceSource.toUpperCase()}
                </div>
              </div>
            </Card>
          </section>
        </>
      )}
    </div>
  );
}
