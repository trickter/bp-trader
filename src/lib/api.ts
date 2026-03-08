import type {
  AccountEvent,
  AlertEvent,
  AssetBalance,
  BacktestResult,
  ExchangeAccount,
  MarketMetric,
  Position,
  ProfileSummary,
  StrategySummary,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export const api = {
  profileSummary: () => getJson<ProfileSummary>("/api/profile/summary"),
  profileAssets: () => getJson<AssetBalance[]>("/api/profile/assets"),
  profilePositions: () => getJson<Position[]>("/api/profile/positions"),
  accountEvents: () => getJson<AccountEvent[]>("/api/profile/account-events"),
  strategies: () => getJson<StrategySummary[]>("/api/strategies"),
  backtest: () => getJson<BacktestResult>("/api/backtests/demo"),
  marketPulse: () => getJson<MarketMetric[]>("/api/markets/pulse"),
  alerts: () => getJson<AlertEvent[]>("/api/alerts"),
  exchangeAccounts: () => getJson<ExchangeAccount[]>("/api/settings/accounts"),
};
