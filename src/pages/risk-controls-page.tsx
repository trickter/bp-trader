import { useEffect, useState } from "react";

import { LoadingBlock, SectionState } from "../components/async-state";
import { Card } from "../components/ui/card";
import { SectionTitle } from "../components/ui/section-title";
import { api } from "../lib/api";
import type { RiskControls } from "../lib/types";

const fieldClassName =
  "w-full appearance-none rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-900";

const EMPTY_CONTROLS: RiskControls = {
  maxOpenPositions: 3,
  maxConsecutiveLoss: 3,
  maxSymbolExposure: 150,
  stopLossPercent: 10,
  maxTradeRisk: 10,
  maxSlippagePercent: 0.4,
  maxSpreadPercent: 0.3,
  volatilityFilterPercent: 8,
  maxPositionNotional: 300,
  dailyLossLimit: 15,
  maxLeverage: 3,
  allowedSymbols: ["BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP", "DOGE_USDC_PERP", "BNB_USDC_PERP"],
  tradingWindowStart: "00:00",
  tradingWindowEnd: "23:59",
  killSwitchEnabled: false,
  requireMarkPrice: true,
  updatedAt: "",
};

function mergeRiskControls(payload: Partial<RiskControls> | null | undefined): RiskControls {
  return {
    ...EMPTY_CONTROLS,
    ...payload,
    allowedSymbols: payload?.allowedSymbols ?? EMPTY_CONTROLS.allowedSymbols,
  };
}

export function RiskControlsPage() {
  const [controls, setControls] = useState<RiskControls>(EMPTY_CONTROLS);
  const [baseline, setBaseline] = useState<RiskControls>(EMPTY_CONTROLS);
  const [symbols, setSymbols] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const hasPendingChanges = JSON.stringify(controls) !== JSON.stringify(baseline);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const [riskPayload, symbolRows] = await Promise.all([api.riskControls(), api.marketSymbols()]);
        if (!active) {
          return;
        }
        const normalized = mergeRiskControls(riskPayload);
        setControls(normalized);
        setBaseline(normalized);
        setSymbols(symbolRows);
      } catch (cause: unknown) {
        if (!active) {
          return;
        }
        setError(cause instanceof Error ? cause.message : "Unknown error");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  function toggleSymbol(symbol: string) {
    setControls((current) => ({
      ...current,
      allowedSymbols: current.allowedSymbols.includes(symbol)
        ? current.allowedSymbols.filter((item) => item !== symbol)
        : [...current.allowedSymbols, symbol],
    }));
  }

  async function handleSave() {
    setSaving(true);
    setMessage(null);
    setError(null);

    try {
      const saved = mergeRiskControls(await api.updateRiskControls(controls));
      setControls(saved);
      setBaseline(saved);
      setMessage("Risk controls updated.");
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "Unknown error");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <LoadingBlock rows={1} className="h-72" />;
  }

  if (error && controls.updatedAt === "") {
    return <SectionState title="Risk controls failed to load" detail={error} tone="error" />;
  }

  return (
    <Card>
      <SectionTitle
        eyebrow="Risk posture"
        title="Control frame"
        description="Set the explicit risk envelope by account, strategy, trade, and market layer instead of relying on placeholder policy text."
      />
      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="grid gap-4">
          <div className="rounded-xl border border-gray-100 bg-gray-50 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="ui-kicker text-[10px] font-semibold text-gray-400">Account level</p>
              <p className="financial-data text-xs text-gray-500">
                {controls.maxPositionNotional}U notional / {controls.maxLeverage.toFixed(1)}x / {controls.dailyLossLimit}U daily loss
              </p>
            </div>
            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                <span>Max position notional</span>
                <input
                  className={fieldClassName}
                  type="number"
                  min="0"
                  value={controls.maxPositionNotional}
                  onChange={(event) =>
                    setControls((current) => ({ ...current, maxPositionNotional: Number(event.target.value) }))
                  }
                />
              </label>
              <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                <span>Daily loss limit</span>
                <input
                  className={fieldClassName}
                  type="number"
                  min="0"
                  value={controls.dailyLossLimit}
                  onChange={(event) =>
                    setControls((current) => ({ ...current, dailyLossLimit: Number(event.target.value) }))
                  }
                />
              </label>
              <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                <span>Max leverage</span>
                <input
                  className={fieldClassName}
                  type="number"
                  min="1"
                  step="0.1"
                  value={controls.maxLeverage}
                  onChange={(event) =>
                    setControls((current) => ({ ...current, maxLeverage: Number(event.target.value) }))
                  }
                />
              </label>
            </div>
          </div>

          <div className="rounded-xl border border-gray-100 bg-gray-50 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="ui-kicker text-[10px] font-semibold text-gray-400">Strategy level</p>
              <p className="financial-data text-xs text-gray-500">
                {controls.maxOpenPositions} open / {controls.maxConsecutiveLoss} loss streak / {controls.maxSymbolExposure}U symbol cap
              </p>
            </div>
            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                <span>Max open positions</span>
                <input
                  className={fieldClassName}
                  type="number"
                  min="1"
                  value={controls.maxOpenPositions}
                  onChange={(event) =>
                    setControls((current) => ({ ...current, maxOpenPositions: Number(event.target.value) }))
                  }
                />
              </label>
              <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                <span>Max consecutive loss</span>
                <input
                  className={fieldClassName}
                  type="number"
                  min="1"
                  value={controls.maxConsecutiveLoss}
                  onChange={(event) =>
                    setControls((current) => ({ ...current, maxConsecutiveLoss: Number(event.target.value) }))
                  }
                />
              </label>
              <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                <span>Max symbol exposure</span>
                <input
                  className={fieldClassName}
                  type="number"
                  min="0"
                  value={controls.maxSymbolExposure}
                  onChange={(event) =>
                    setControls((current) => ({ ...current, maxSymbolExposure: Number(event.target.value) }))
                  }
                />
              </label>
            </div>
          </div>

          <div className="rounded-xl border border-gray-100 bg-gray-50 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="ui-kicker text-[10px] font-semibold text-gray-400">Trade level</p>
              <p className="financial-data text-xs text-gray-500">
                {controls.stopLossPercent}% stop / {controls.maxTradeRisk}U risk / {controls.maxSlippagePercent}% slippage
              </p>
            </div>
            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                <span>Stop loss (%)</span>
                <input
                  className={fieldClassName}
                  type="number"
                  min="0"
                  step="0.1"
                  value={controls.stopLossPercent}
                  onChange={(event) =>
                    setControls((current) => ({ ...current, stopLossPercent: Number(event.target.value) }))
                  }
                />
              </label>
              <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                <span>Max trade risk</span>
                <input
                  className={fieldClassName}
                  type="number"
                  min="0"
                  step="0.1"
                  value={controls.maxTradeRisk}
                  onChange={(event) =>
                    setControls((current) => ({ ...current, maxTradeRisk: Number(event.target.value) }))
                  }
                />
              </label>
              <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                <span>Max slippage (%)</span>
                <input
                  className={fieldClassName}
                  type="number"
                  min="0"
                  step="0.1"
                  value={controls.maxSlippagePercent}
                  onChange={(event) =>
                    setControls((current) => ({ ...current, maxSlippagePercent: Number(event.target.value) }))
                  }
                />
              </label>
            </div>
          </div>

          <div className="rounded-xl border border-gray-100 bg-gray-50 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="ui-kicker text-[10px] font-semibold text-gray-400">Market level</p>
              <p className="financial-data text-xs text-gray-500">
                {controls.maxSpreadPercent}% spread / {controls.volatilityFilterPercent}% volatility gate
              </p>
            </div>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                <span>Max spread (%)</span>
                <input
                  className={fieldClassName}
                  type="number"
                  min="0"
                  step="0.1"
                  value={controls.maxSpreadPercent}
                  onChange={(event) =>
                    setControls((current) => ({ ...current, maxSpreadPercent: Number(event.target.value) }))
                  }
                />
              </label>
              <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                <span>Volatility filter (%)</span>
                <input
                  className={fieldClassName}
                  type="number"
                  min="0"
                  step="0.1"
                  value={controls.volatilityFilterPercent}
                  onChange={(event) =>
                    setControls((current) => ({ ...current, volatilityFilterPercent: Number(event.target.value) }))
                  }
                />
              </label>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="grid gap-1.5 text-xs font-medium text-gray-700">
              <span>Trading window start</span>
              <input
                className={fieldClassName}
                type="time"
                value={controls.tradingWindowStart}
                onChange={(event) =>
                  setControls((current) => ({ ...current, tradingWindowStart: event.target.value }))
                }
              />
            </label>
            <label className="grid gap-1.5 text-xs font-medium text-gray-700">
              <span>Trading window end</span>
              <input
                className={fieldClassName}
                type="time"
                value={controls.tradingWindowEnd}
                onChange={(event) =>
                  setControls((current) => ({ ...current, tradingWindowEnd: event.target.value }))
                }
              />
            </label>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700 transition hover:border-gray-300">
              <input
                type="checkbox"
                className="accent-gray-900"
                checked={controls.killSwitchEnabled}
                onChange={(event) =>
                  setControls((current) => ({ ...current, killSwitchEnabled: event.target.checked }))
                }
              />
              Kill switch enabled
            </label>
            <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700 transition hover:border-gray-300">
              <input
                type="checkbox"
                className="accent-gray-900"
                checked={controls.requireMarkPrice}
                onChange={(event) =>
                  setControls((current) => ({ ...current, requireMarkPrice: event.target.checked }))
                }
              />
              Require mark price for risk checks
            </label>
          </div>
          {error ? <SectionState title="Risk controls save failed" detail={error} tone="error" /> : null}
          {message ? <SectionState title="Risk controls updated" detail={message} /> : null}
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="rounded-full bg-gray-900 px-5 py-2 text-sm font-semibold text-white transition hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? "Saving..." : "Save controls"}
            </button>
            <button
              type="button"
              onClick={() => {
                setControls(baseline);
                setMessage(null);
                setError(null);
              }}
              className="rounded-full border border-gray-200 px-5 py-2 text-sm text-gray-600 transition hover:border-gray-900 hover:text-gray-900"
            >
              Reset
            </button>
            <div className="flex items-center rounded-full border border-gray-100 bg-gray-50 px-4 py-2 text-sm text-gray-500">
              {hasPendingChanges ? "Unsaved changes" : "Saved values loaded"}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <Card>
            <SectionTitle
              eyebrow="Allowlist"
              title="Tradable symbols"
              description="Choose which contracts remain available to strategy execution and backtest defaults."
            />
            <div className="grid gap-2">
              {symbols.map((symbol) => (
                <label
                  key={symbol}
                  className="flex cursor-pointer items-center gap-3 rounded-xl border border-gray-100 bg-white px-4 py-3 text-sm text-gray-700 transition hover:border-gray-200"
                >
                  <input
                    type="checkbox"
                    className="accent-gray-900"
                    checked={controls.allowedSymbols.includes(symbol)}
                    onChange={() => toggleSymbol(symbol)}
                  />
                  {symbol}
                </label>
              ))}
            </div>
          </Card>
          <Card>
            <SectionTitle
              eyebrow="Audit"
              title="Current envelope"
              description="The effective risk values below mirror the currently loaded controls, so changes are visible immediately after save."
            />
            <div className="space-y-2 text-xs text-gray-500">
              <div className="rounded-xl border border-blue-100 bg-blue-50 p-3.5">
                Save state:{" "}
                <span className="font-semibold text-blue-700">
                  {hasPendingChanges ? "Editing values differ from last saved state" : "Inputs match last saved state"}
                </span>
              </div>
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-3.5">
                Account: <span className="financial-data font-semibold text-gray-900">{controls.maxPositionNotional}U max notional / {controls.maxLeverage.toFixed(1)}x / {controls.dailyLossLimit}U daily loss</span>
              </div>
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-3.5">
                Strategy: <span className="financial-data font-semibold text-gray-900">{controls.maxOpenPositions} open / {controls.maxConsecutiveLoss} loss streak / {controls.maxSymbolExposure}U per symbol</span>
              </div>
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-3.5">
                Trade: <span className="financial-data font-semibold text-gray-900">{controls.stopLossPercent}% stop / {controls.maxTradeRisk}U max risk / {controls.maxSlippagePercent}% slippage</span>
              </div>
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-3.5">
                Market: <span className="financial-data font-semibold text-gray-900">{controls.maxSpreadPercent}% spread / {controls.volatilityFilterPercent}% volatility filter</span>
              </div>
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-3.5">
                Allowed symbols: <span className="font-semibold text-gray-900">{controls.allowedSymbols.join(", ") || "None"}</span>
              </div>
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-3.5">
                Updated at: <span className="financial-data font-semibold text-gray-900">{controls.updatedAt || "Pending first save"}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </Card>
  );
}
