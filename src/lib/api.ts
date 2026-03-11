import type {
  AccountEvent,
  AgentCapability,
  AgentContext,
  AlertEvent,
  AssetBalance,
  BacktestRequest,
  BacktestResult,
  BacktestRunAccepted,
  ExecutionEvent,
  ExecutionOrder,
  ExecutionRuntimeCommand,
  ExecutionRuntimeStatus,
  ExchangeAccount,
  LiveStrategyEnableRequest,
  LiveStrategyExecution,
  MarketMetric,
  Position,
  ProfileSummary,
  RiskControls,
  StrategySummary,
  StrategyUpsertRequest,
} from "./types";
import { clearAdminToken, getAdminToken, notifyInvalidAdminToken } from "./admin-token";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  status: number;
  code?: string;
  retryable?: boolean;

  constructor(message: string, status: number, code?: string, retryable?: boolean) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.retryable = retryable;
  }
}

async function getJson<T>(path: string): Promise<T> {
  return requestJson<T>(path, { method: "GET" });
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

async function putJson<T>(path: string, body: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
  const adminToken = getAdminToken();
  const headers = new Headers();

  if (adminToken) {
    headers.set("X-Admin-Token", adminToken);
  }
  if (init.body) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;
    let code: string | undefined;
    let retryable: boolean | undefined;

    try {
      const payload = (await response.json()) as {
        detail?: string | { message?: string; code?: string; retryable?: boolean };
      };
      if (typeof payload.detail === "string") {
        message = payload.detail;
      } else if (payload.detail && typeof payload.detail.message === "string") {
        message = payload.detail.message;
        code = payload.detail.code;
        retryable = payload.detail.retryable;
      }
    } catch {
      // Ignore JSON parsing errors and keep the HTTP-derived message.
    }

    if (response.status === 401 || response.status === 403) {
      clearAdminToken();
      notifyInvalidAdminToken();
    }

    throw new ApiError(message, response.status, code, retryable);
  }

  return (await response.json()) as T;
}

export const api = {
  profileSummary: () => getJson<ProfileSummary>("/api/profile/summary"),
  profileAssets: () => getJson<AssetBalance[]>("/api/profile/assets"),
  profilePositions: () => getJson<Position[]>("/api/profile/positions"),
  accountEvents: () => getJson<AccountEvent[]>("/api/profile/account-events"),
  strategies: () => getJson<StrategySummary[]>("/api/strategies"),
  createStrategy: (request: StrategyUpsertRequest) => postJson<StrategySummary>("/api/strategies", request),
  updateStrategy: (strategyId: string, request: StrategyUpsertRequest) =>
    putJson<StrategySummary>(`/api/strategies/${strategyId}`, request),
  liveStrategies: () => getJson<LiveStrategyExecution[]>("/api/execution/live-strategies"),
  enableLiveStrategy: (strategyId: string, request: LiveStrategyEnableRequest) =>
    postJson<LiveStrategyExecution>(`/api/execution/live-strategies/${strategyId}/enable`, request),
  disableLiveStrategy: (strategyId: string) =>
    postJson<LiveStrategyExecution>(`/api/execution/live-strategies/${strategyId}/disable`, {}),
  flattenLiveStrategy: (strategyId: string, request: ExecutionRuntimeCommand) =>
    postJson<LiveStrategyExecution>(`/api/execution/live-strategies/${strategyId}/flatten`, request),
  disableAndFlattenLiveStrategy: (strategyId: string, request: ExecutionRuntimeCommand) =>
    postJson<LiveStrategyExecution>(`/api/execution/live-strategies/${strategyId}/disable-and-flatten`, request),
  executionRuntime: () => getJson<ExecutionRuntimeStatus>("/api/execution/runtime"),
  startExecutionRuntime: (request: ExecutionRuntimeCommand) =>
    postJson<ExecutionRuntimeStatus>("/api/execution/runtime/start", request),
  stopExecutionRuntime: (request: ExecutionRuntimeCommand) =>
    postJson<ExecutionRuntimeStatus>("/api/execution/runtime/stop", request),
  executionOrders: () => getJson<ExecutionOrder[]>("/api/execution/orders"),
  executionEvents: () => getJson<ExecutionEvent[]>("/api/execution/events"),
  createTemplateBacktest: (templateId: string, request: BacktestRequest) =>
    postJson<BacktestRunAccepted>(`/api/strategies/templates/${templateId}/backtests`, request),
  createScriptBacktest: (strategyId: string, request: BacktestRequest) =>
    postJson<BacktestRunAccepted>(`/api/strategies/scripts/${strategyId}/backtests`, request),
  getBacktest: (backtestId: string) => getJson<BacktestResult>(`/api/backtests/${backtestId}`),
  marketPulse: (symbol?: string) =>
    getJson<MarketMetric[]>(symbol ? `/api/markets/pulse/${encodeURIComponent(symbol)}` : "/api/markets/pulse"),
  marketSymbols: () => getJson<string[]>("/api/markets/symbols"),
  alerts: () => getJson<AlertEvent[]>("/api/alerts"),
  riskControls: () => getJson<RiskControls>("/api/risk-controls"),
  updateRiskControls: (request: RiskControls) => putJson<RiskControls>("/api/risk-controls", request),
  exchangeAccounts: () => getJson<ExchangeAccount[]>("/api/settings/accounts"),
  agentCapabilities: () => getJson<AgentCapability[]>("/api/agent/capabilities"),
  agentContext: () => getJson<AgentContext>("/api/agent/context"),
};
