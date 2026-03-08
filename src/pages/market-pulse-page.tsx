import { useEffect, useState } from "react";

import { LoadingBlock, SectionState } from "../components/async-state";
import { Card } from "../components/ui/card";
import { SectionTitle } from "../components/ui/section-title";
import { StatusPill } from "../components/ui/status-pill";
import { api } from "../lib/api";
import type { MarketMetric } from "../lib/types";

const fieldClassName =
  "w-full appearance-none rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40";

function normalizeFundingMetric(metric: MarketMetric) {
  if (metric.label !== "Funding rate") {
    return metric;
  }

  const numeric = Number.parseFloat(metric.value.replace("%", ""));
  if (Number.isNaN(numeric)) {
    return metric;
  }

  return {
    ...metric,
    value: `${numeric >= 0 ? "+" : ""}${numeric.toFixed(3)}%`,
  };
}

export function MarketPulsePage() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState("BTC_USDC_PERP");
  const [metrics, setMetrics] = useState<MarketMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadSymbols() {
      try {
        const rows = await api.marketSymbols();
        if (!active) {
          return;
        }
        setSymbols(rows);
        if (rows[0]) {
          setSelectedSymbol((current) => current || rows[0]);
        }
      } catch (cause: unknown) {
        if (active) {
          setError(cause instanceof Error ? cause.message : "Unknown error");
          setLoading(false);
        }
      }
    }

    void loadSymbols();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadMetrics() {
      setLoading(true);
      setError(null);

      try {
        const rows = await api.marketPulse(selectedSymbol);
        if (!active) {
          return;
        }
        setMetrics(rows.map(normalizeFundingMetric));
      } catch (cause: unknown) {
        if (!active) {
          return;
        }
        setMetrics([]);
        setError(cause instanceof Error ? cause.message : "Unknown error");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadMetrics();
    return () => {
      active = false;
    };
  }, [selectedSymbol]);

  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <SectionTitle
          eyebrow="Refresh semantics"
          title="Market pulse"
          description="Switch across contracts, with funding rate rendered as a percentage and each tile keeping its own freshness contract."
        />
        <div className="w-full max-w-xs">
          <select
            className={fieldClassName}
            style={{ colorScheme: "dark" }}
            value={selectedSymbol}
            onChange={(event) => setSelectedSymbol(event.target.value)}
          >
            {symbols.map((symbol) => (
              <option className="bg-slate-950 text-slate-100" key={symbol} value={symbol}>
                {symbol}
              </option>
            ))}
          </select>
        </div>
      </div>
      {loading ? (
        <LoadingBlock rows={6} className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" />
      ) : error ? (
        <SectionState title="Market pulse failed to load" detail={error} tone="error" />
      ) : metrics.length === 0 ? (
        <SectionState
          title="No market pulse metrics"
          detail="The exchange did not return any freshness-aware metrics for this contract."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {metrics.map((metric) => (
            <div
              key={`${selectedSymbol}-${metric.label}`}
              className="rounded-[24px] border border-white/8 bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.02))] p-5"
            >
              <div className="mb-5 flex items-center justify-between gap-3">
                <p className="text-sm text-slate-300">{metric.label}</p>
                <StatusPill tone={metric.tone}>{metric.freshness}</StatusPill>
              </div>
              <p className="text-3xl font-semibold text-white">{metric.value}</p>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
