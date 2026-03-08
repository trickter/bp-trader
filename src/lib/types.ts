export type PriceSource = "last" | "mark" | "index";

export interface ProfileSummary {
  totalEquity: number;
  availableMargin: number;
  unrealizedPnl: number;
  realizedPnl24h: number;
  winRate: number;
  riskLevel: string;
  priceSource: PriceSource;
  syncedAt: string;
}

export interface AssetBalance {
  asset: string;
  available: number;
  locked: number;
  collateralValue: number;
  portfolioWeight: number;
  change24h: number;
}

export interface Position {
  symbol: string;
  side: "long" | "short";
  quantity: number;
  entryPrice: number;
  markPrice: number;
  liquidationPrice: number | null;
  unrealizedPnl: number;
  marginUsed: number;
  openedAt: string;
  priceSource: PriceSource;
}

export interface AccountEvent {
  id: string;
  eventType:
    | "trade_fill"
    | "funding_settlement"
    | "fee_charge"
    | "deposit"
    | "withdrawal"
    | "liquidation"
    | "adl"
    | "collateral_conversion"
    | "manual_adjustment";
  eventOrigin: "strategy" | "manual" | "system" | "risk";
  asset: string;
  amount: number;
  pnlEffect: number;
  positionEffect: string;
  occurredAt: string;
}

export interface StrategySummary {
  id: string;
  name: string;
  kind: "template" | "script";
  market: string;
  runtime: "disabled" | "paper" | "live-ready";
  status: "healthy" | "idle" | "paused";
  lastBacktest: string;
  sharpe: number;
  priceSource: PriceSource;
}

export interface TradeMarker {
  id: string;
  timestamp: string;
  type: "open" | "close";
  side: "long" | "short";
  price: number;
  reason: string;
}

export interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface BacktestResult {
  id: string;
  strategyName: string;
  priceSource: PriceSource;
  totalReturn: number;
  maxDrawdown: number;
  sharpe: number;
  winRate: number;
  candles: Candle[];
  tradeMarkers: TradeMarker[];
  equityCurve: Array<{ timestamp: string; equity: number }>;
}

export interface MarketMetric {
  label: string;
  value: string;
  freshness: string;
  tone?: "positive" | "negative" | "neutral";
}

export interface AlertEvent {
  id: string;
  level: "info" | "warning" | "critical";
  title: string;
  detail: string;
  occurredAt: string;
}

export interface ExchangeAccount {
  id: string;
  exchange: string;
  label: string;
  marketType: string;
  lastCredentialRotation: string;
  status: "healthy" | "attention";
}
