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
  origin: "strategy" | "manual" | "system" | "risk";
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
  description: string;
  market: string;
  accountId: string;
  runtime: "disabled" | "paper" | "live-ready";
  status: "healthy" | "idle" | "paused";
  lastBacktest: string;
  sharpe: number;
  priceSource: PriceSource;
  parameters: Record<string, string | number | boolean>;
}

export interface ExecutionBudgetAllocation {
  strategyId: string;
  strategyName: string;
  weight: number;
  budgetNotional: number;
}

export interface LiveStrategyExecution {
  strategyId: string;
  strategyName: string;
  strategyKind: "template" | "script";
  market: string;
  accountId: string;
  priceSource: PriceSource;
  runtimeStatus: string;
  liveEnabled: boolean;
  isWhitelisted: boolean;
  executionWeight: number;
  pollIntervalSeconds: number;
  confirmedAt?: string | null;
  lastCycleAt?: string | null;
  lastSignal?: string | null;
  lastError?: string | null;
  lastOrderId?: string | null;
  readinessChecks: string[];
}

export interface TradeMarker {
  id: string;
  timestamp: string;
  candleTimestamp: string;
  action: "open" | "add" | "reduce" | "close" | "stop" | "take_profit";
  type: "open" | "add" | "reduce" | "close" | "stop" | "take_profit";
  side: "long" | "short";
  price: number;
  qty: number;
  reason: string;
  relatedTradeId: string;
  relatedOrderId: string;
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
  strategyId: string;
  strategyKind: "template" | "script";
  strategyName: string;
  exchangeId: string;
  marketType: string;
  symbol: string;
  interval: string;
  startTime: number;
  endTime: number;
  priceSource: PriceSource;
  chartPriceSource: PriceSource;
  feeBps: number;
  slippageBps: number;
  status: "queued" | "running" | "completed" | "failed";
  createdAt: string;
  completedAt: string;
  totalReturn: number;
  maxDrawdown: number;
  sharpe: number;
  winRate: number;
  candles: Candle[];
  tradeMarkers: TradeMarker[];
  equityCurve: Array<{ timestamp: string; equity: number }>;
  chartWarnings: string[];
}

export interface BacktestRequest {
  symbol: string;
  interval: string;
  startTime: number;
  endTime: number;
  priceSource: PriceSource;
  feeBps: number;
  slippageBps: number;
}

export interface BacktestRunAccepted {
  id: string;
  strategyId: string;
  strategyKind: "template" | "script";
  status: "queued" | "running" | "completed" | "failed";
  createdAt: string;
  resultPath: string;
  pollAfterMs: number;
  demoMode: boolean;
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

export interface StrategyUpsertRequest {
  name: string;
  kind: "template" | "script";
  description: string;
  market: string;
  accountId: string;
  runtime: "disabled" | "paper" | "live-ready";
  status: "healthy" | "idle" | "paused";
  priceSource: PriceSource;
  parameters: Record<string, string | number | boolean>;
}

export interface RiskControls {
  maxOpenPositions: number;
  maxConsecutiveLoss: number;
  maxSymbolExposure: number;
  stopLossPercent: number;
  maxTradeRisk: number;
  maxSlippagePercent: number;
  maxSpreadPercent: number;
  volatilityFilterPercent: number;
  maxPositionNotional: number;
  dailyLossLimit: number;
  maxLeverage: number;
  allowedSymbols: string[];
  tradingWindowStart: string;
  tradingWindowEnd: string;
  killSwitchEnabled: boolean;
  requireMarkPrice: boolean;
  updatedAt: string;
}

export interface ExecutionOrder {
  id: string;
  strategyId: string;
  strategyName: string;
  clientOrderId: string;
  exchangeOrderId: string;
  symbol: string;
  side: string;
  action: string;
  status: string;
  quantity: number;
  price: number;
  reduceOnly: boolean;
  submittedAt: string;
  updatedAt: string;
  failureReason: string;
}

export interface ExecutionEvent {
  id: string;
  strategyId: string;
  strategyName: string;
  level: "info" | "warning" | "critical" | string;
  eventType: string;
  message: string;
  symbol?: string;
  signal?: string;
  createdAt: string;
  metadata: Record<string, string | number | boolean>;
}

export interface ExecutionRuntimeStatus {
  mode: string;
  running: boolean;
  maxConcurrentStrategies: number;
  activeStrategyCount: number;
  enabledStrategyCount: number;
  budgets: ExecutionBudgetAllocation[];
  warnings: string[];
  startedAt?: string | null;
  stoppedAt?: string | null;
  lastCycleAt?: string | null;
  lastError?: string | null;
}

export interface LiveStrategyEnableRequest {
  confirmed: boolean;
}

export interface ExecutionRuntimeCommand {
  confirmed: boolean;
  reason: string;
}

export interface AgentCapability {
  id: string;
  label: string;
  description: string;
  readOnly: boolean;
  route: string;
  entity: string;
}

export interface AgentContext {
  mode: string;
  accountMode: string;
  availableCapabilities: string[];
  capabilities: AgentCapability[];
  domainVocabulary: string[];
  resources: Record<string, string>;
}
