import { useEffect, useState } from "react";

import { LoadingBlock, SectionState } from "../components/async-state";
import { Card } from "../components/ui/card";
import { SectionTitle } from "../components/ui/section-title";
import { StatusPill } from "../components/ui/status-pill";
import { api } from "../lib/api";
import { formatCurrency } from "../lib/utils";
import type { ExecutionEvent, ExecutionOrder, ExecutionRuntimeStatus, LiveStrategyExecution } from "../lib/types";

type LoadState = "loading" | "ready" | "error";

function runtimeTone(running: boolean) {
  return running ? "positive" as const : "neutral" as const;
}

function eventTone(level: string) {
  if (level === "critical") return "negative" as const;
  if (level === "warning") return "neutral" as const;
  return "positive" as const;
}

export function ExecutionPage() {
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [runtime, setRuntime] = useState<ExecutionRuntimeStatus | null>(null);
  const [liveStrategies, setLiveStrategies] = useState<LiveStrategyExecution[]>([]);
  const [orders, setOrders] = useState<ExecutionOrder[]>([]);
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [pendingAction, setPendingAction] = useState<"start" | "stop" | null>(null);
  const [pendingStrategyAction, setPendingStrategyAction] = useState<string | null>(null);

  async function load() {
    try {
      const [runtimePayload, strategiesPayload, ordersPayload, eventsPayload] = await Promise.all([
        api.executionRuntime(),
        api.liveStrategies(),
        api.executionOrders(),
        api.executionEvents(),
      ]);
      setRuntime(runtimePayload);
      setLiveStrategies(strategiesPayload);
      setOrders(ordersPayload);
      setEvents(eventsPayload);
      setLoadState("ready");
      setLoadError(null);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Unknown error");
      setLoadState("error");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleStart() {
    setPendingAction("start");
    try {
      await api.startExecutionRuntime({ confirmed: true, reason: "manual start from admin console" });
      await load();
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Execution runtime failed to start");
      setLoadState("error");
    } finally {
      setPendingAction(null);
    }
  }

  async function handleStop() {
    setPendingAction("stop");
    try {
      await api.stopExecutionRuntime({ confirmed: true, reason: "manual stop from admin console" });
      await load();
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Execution runtime failed to stop");
      setLoadState("error");
    } finally {
      setPendingAction(null);
    }
  }

  async function handleFlatten(strategyId: string) {
    setPendingStrategyAction(`flatten:${strategyId}`);
    try {
      await api.flattenLiveStrategy(strategyId, { confirmed: true, reason: "manual flatten from execution page" });
      await load();
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Manual flatten failed");
      setLoadState("error");
    } finally {
      setPendingStrategyAction(null);
    }
  }

  async function handleDisableAndFlatten(strategyId: string) {
    setPendingStrategyAction(`disable:${strategyId}`);
    try {
      await api.disableAndFlattenLiveStrategy(strategyId, {
        confirmed: true,
        reason: "disable and flatten from execution page",
      });
      await load();
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Disable and flatten failed");
      setLoadState("error");
    } finally {
      setPendingStrategyAction(null);
    }
  }

  if (loadState === "loading") {
    return <LoadingBlock rows={8} />;
  }

  if (loadState === "error" && !runtime) {
    return <SectionState title="Execution runtime failed to load" detail={loadError ?? "Unknown error"} tone="error" />;
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[1.3fr_1fr]">
        <Card>
          <SectionTitle
            eyebrow="Live runtime"
            title="Execution control"
            description="Start or stop the polling runtime, inspect budgets, and watch the current live strategy pool."
          />
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-xl border border-gray-100 bg-gray-50 p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">Runtime</span>
                <StatusPill tone={runtimeTone(Boolean(runtime?.running))}>{runtime?.running ? "running" : "stopped"}</StatusPill>
              </div>
              <div className="mt-3 font-sans text-lg font-semibold text-gray-900">{runtime?.mode ?? "live"}</div>
            </div>
            <div className="rounded-xl border border-gray-100 bg-gray-50 p-4">
              <div className="text-xs text-gray-500">Enabled strategies</div>
              <div className="financial-data mt-3 text-lg font-semibold text-gray-900">{runtime?.enabledStrategyCount ?? 0}</div>
            </div>
            <div className="rounded-xl border border-gray-100 bg-gray-50 p-4">
              <div className="text-xs text-gray-500">Active strategies</div>
              <div className="financial-data mt-3 text-lg font-semibold text-gray-900">{runtime?.activeStrategyCount ?? 0}</div>
            </div>
            <div className="rounded-xl border border-gray-100 bg-gray-50 p-4">
              <div className="text-xs text-gray-500">Parallel cap</div>
              <div className="financial-data mt-3 text-lg font-semibold text-gray-900">{runtime?.maxConcurrentStrategies ?? 0}</div>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void handleStart()}
              disabled={pendingAction !== null}
              className="rounded-full bg-gray-900 px-4 py-2 text-xs font-semibold text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-gray-300"
            >
              {pendingAction === "start" ? "Starting..." : "Start runtime"}
            </button>
            <button
              type="button"
              onClick={() => void handleStop()}
              disabled={pendingAction !== null}
              className="rounded-full border border-gray-200 px-4 py-2 text-xs font-semibold text-gray-700 transition hover:border-gray-900 hover:text-gray-900 disabled:cursor-not-allowed disabled:text-gray-300"
            >
              {pendingAction === "stop" ? "Stopping..." : "Stop runtime"}
            </button>
            <button
              type="button"
              onClick={() => void load()}
              className="rounded-full border border-gray-200 px-4 py-2 text-xs font-semibold text-gray-700 transition hover:border-gray-900 hover:text-gray-900"
            >
              Refresh
            </button>
          </div>
          {runtime?.warnings?.length ? (
            <div className="mt-4 rounded-xl border border-amber-100 bg-amber-50 px-4 py-3 text-xs text-amber-700">
              {runtime.warnings.join(" ")}
            </div>
          ) : null}
        </Card>

        <Card>
          <SectionTitle
            eyebrow="Budget allocation"
            title="Execution weights"
            description="The live pool shares the account notional cap across enabled strategies."
          />
          <div className="space-y-3">
            {runtime?.budgets?.length ? (
              runtime.budgets.map((item) => (
                <div key={item.strategyId} className="rounded-xl border border-gray-100 bg-gray-50 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-gray-900">{item.strategyName}</span>
                    <span className="financial-data text-xs text-gray-500">weight {item.weight.toFixed(2)}</span>
                  </div>
                  <div className="financial-data mt-2 text-sm text-gray-600">{formatCurrency(item.budgetNotional)} notional budget</div>
                </div>
              ))
            ) : (
              <div className="rounded-xl border border-dashed border-gray-200 px-4 py-5 text-sm text-gray-500">
                No active budget allocation yet.
              </div>
            )}
          </div>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_1fr_1fr]">
        <Card>
          <SectionTitle
            eyebrow="Live strategies"
            title="Whitelisted strategy pool"
            description="Only confirmed and whitelisted strategies can join the live runtime."
          />
          <div className="space-y-3">
            {liveStrategies.map((item) => (
              <div key={item.strategyId} className="rounded-xl border border-gray-100 bg-gray-50 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-gray-900">{item.strategyName}</div>
                    <div className="mt-1 text-xs text-gray-500">{item.market}</div>
                  </div>
                  <StatusPill tone={item.runtimeStatus === "live_active" ? "positive" : "neutral"}>{item.runtimeStatus}</StatusPill>
                </div>
                <div className="mt-3 grid gap-2 text-xs text-gray-600 md:grid-cols-2">
                  <div className="financial-data">Weight: {item.executionWeight.toFixed(2)}</div>
                  <div className="financial-data">Poll: {item.pollIntervalSeconds}s</div>
                  <div>Whitelist: {item.liveEnabled ? "on" : "off"}</div>
                  <div>Confirmed: {item.confirmedAt ? "yes" : "no"}</div>
                </div>
                <div className="mt-3 flex gap-2">
                  <button
                    type="button"
                    onClick={() => void handleFlatten(item.strategyId)}
                    disabled={pendingStrategyAction !== null}
                    className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-[11px] font-semibold text-gray-700 transition hover:border-gray-900 hover:text-gray-900 disabled:cursor-not-allowed disabled:text-gray-300"
                  >
                    {pendingStrategyAction === `flatten:${item.strategyId}` ? "Flattening..." : "Flatten"}
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleDisableAndFlatten(item.strategyId)}
                    disabled={pendingStrategyAction !== null}
                    className="flex-1 rounded-lg bg-gray-900 px-3 py-2 text-[11px] font-semibold text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-gray-300"
                  >
                    {pendingStrategyAction === `disable:${item.strategyId}` ? "Working..." : "Disable & Flatten"}
                  </button>
                </div>
                {item.lastError ? (
                  <div className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">{item.lastError}</div>
                ) : null}
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <SectionTitle
            eyebrow="Recent orders"
            title="Market order feed"
            description="Most recent execution orders with explicit client ids and statuses."
          />
          <div className="space-y-3">
            {orders.length ? (
              orders.slice(0, 8).map((item) => (
                <div key={item.id} className="rounded-xl border border-gray-100 bg-gray-50 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-semibold text-gray-900">{item.strategyName || item.strategyId}</span>
                    <StatusPill tone={item.status === "filled" ? "positive" : "neutral"}>{item.status}</StatusPill>
                  </div>
                  <div className="mt-2 text-xs text-gray-600">
                    {item.symbol} · {item.side} · {item.action}
                  </div>
                  <div className="financial-data mt-1 text-xs text-gray-500">
                    qty {item.quantity} · client {item.clientOrderId}
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-xl border border-dashed border-gray-200 px-4 py-5 text-sm text-gray-500">
                No live orders yet.
              </div>
            )}
          </div>
        </Card>

        <Card>
          <SectionTitle
            eyebrow="Recent events"
            title="Execution event log"
            description="Risk blocks, runtime events, and order submission results are recorded here."
          />
          <div className="space-y-3">
            {events.length ? (
              events.slice(0, 10).map((item) => (
                <div key={item.id} className="rounded-xl border border-gray-100 bg-gray-50 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-semibold text-gray-900">{item.strategyName || item.strategyId}</span>
                    <StatusPill tone={eventTone(item.level)}>{item.level}</StatusPill>
                  </div>
                  <div className="mt-2 text-xs font-medium text-gray-700">{item.eventType}</div>
                  <div className="mt-1 text-xs text-gray-500">{item.message}</div>
                </div>
              ))
            ) : (
              <div className="rounded-xl border border-dashed border-gray-200 px-4 py-5 text-sm text-gray-500">
                No execution events yet.
              </div>
            )}
          </div>
        </Card>
      </div>

      {loadError ? <SectionState title="Execution notice" detail={loadError} /> : null}
    </div>
  );
}
