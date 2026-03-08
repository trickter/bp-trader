import { useState } from "react";

import { api } from "../lib/api";
import type { BacktestRequest, BacktestResult, BacktestRunAccepted } from "../lib/types";

interface UseBacktestRunOptions {
  strategyId?: string;
  strategyKind?: "template" | "script";
  request?: BacktestRequest;
}

const EMPTY_RESULT: BacktestResult = {
  id: "",
  strategyId: "",
  strategyKind: "template",
  strategyName: "",
  exchangeId: "",
  marketType: "",
  symbol: "",
  interval: "",
  startTime: 0,
  endTime: 0,
  priceSource: "mark",
  chartPriceSource: "mark",
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
  chartWarnings: [],
};

export function useBacktestRun({ strategyId, strategyKind, request }: UseBacktestRunOptions) {
  const [run, setRun] = useState<BacktestRunAccepted | null>(null);
  const [result, setResult] = useState<BacktestResult>(EMPTY_RESULT);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runBacktest(override?: UseBacktestRunOptions) {
    const nextStrategyId = override?.strategyId ?? strategyId;
    const nextStrategyKind = override?.strategyKind ?? strategyKind;
    const nextRequest = override?.request ?? request;

    if (!nextStrategyId || !nextStrategyKind || !nextRequest) {
      setError("Strategy selection and request parameters are required.");
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const accepted =
        nextStrategyKind === "template"
          ? await api.createTemplateBacktest(nextStrategyId, nextRequest)
          : await api.createScriptBacktest(nextStrategyId, nextRequest);

      setRun(accepted);

      const payload = await api.getBacktest(accepted.id);
      setResult(payload);
      return payload;
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "Unknown error");
      return null;
    } finally {
      setLoading(false);
    }
  }

  return { run, result, loading, error, runBacktest, hasResult: Boolean(result.id) };
}
