import { useEffect, useState } from "react";

import { api } from "../lib/api";
import type { BacktestRequest, BacktestResult, BacktestRunAccepted } from "../lib/types";

interface UseBacktestRunOptions {
  strategyId: string;
  strategyKind: "template" | "script";
  request: BacktestRequest;
}

const EMPTY_RESULT: BacktestResult = {
  id: "",
  strategyId: "",
  strategyKind: "template",
  strategyName: "",
  symbol: "",
  interval: "",
  startTime: 0,
  endTime: 0,
  priceSource: "mark",
  feeBps: 0,
  slippageBps: 0,
  status: "queued",
  createdAt: "",
  completedAt: "",
  totalReturn: 0,
  maxDrawdown: 0,
  sharpe: 0,
  winRate: 0,
  candles: [],
  tradeMarkers: [],
  equityCurve: [],
};

export function useBacktestRun({ strategyId, strategyKind, request }: UseBacktestRunOptions) {
  const [run, setRun] = useState<BacktestRunAccepted | null>(null);
  const [result, setResult] = useState<BacktestResult>(EMPTY_RESULT);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const accepted =
          strategyKind === "template"
            ? await api.createTemplateBacktest(strategyId, request)
            : await api.createScriptBacktest(strategyId, request);

        if (!active) {
          return;
        }

        setRun(accepted);

        const payload = await api.getBacktest(accepted.id);
        if (!active) {
          return;
        }

        setResult(payload);
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
  }, [
    request.endTime,
    request.feeBps,
    request.interval,
    request.priceSource,
    request.slippageBps,
    request.startTime,
    request.symbol,
    strategyId,
    strategyKind,
  ]);

  return { run, result, loading, error };
}
