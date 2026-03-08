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
import { clearAdminToken, getAdminToken, notifyInvalidAdminToken } from "./admin-token";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const adminToken = getAdminToken();
  const headers = new Headers();

  if (adminToken) {
    headers.set("X-Admin-Token", adminToken);
  }

  const response = await fetch(`${API_BASE}${path}`, { headers });

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      clearAdminToken();
      notifyInvalidAdminToken();
    }

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
