export interface StrategyTemplatePreset {
  id: string;
  label: string;
  summary: string;
  market: string;
  audience: string;
  defaultParameters: Record<string, number | string | boolean>;
}

export interface StrategyIndicatorCategory {
  id: string;
  label: string;
  indicators: string[];
}

export const STRATEGY_TEMPLATE_PRESETS: StrategyTemplatePreset[] = [
  {
    id: "ema_dual_trend",
    label: "EMA 双均线趋势策略",
    summary: "使用快慢 EMA 判断趋势方向并跟随主方向开仓。",
    market: "perpetual",
    audience: "新手",
    defaultParameters: { fast_ema: 9, slow_ema: 21, confirmation_bars: 1 },
  },
  {
    id: "rsi_reversal",
    label: "RSI 超买超卖反转策略",
    summary: "在震荡环境中基于 RSI 极值寻找回归机会。",
    market: "perpetual",
    audience: "新手",
    defaultParameters: { rsi_length: 14, oversold: 30, overbought: 70 },
  },
  {
    id: "macd_trend_follow",
    label: "MACD 趋势跟随策略",
    summary: "MACD 金叉/死叉配合量能过滤做趋势跟随。",
    market: "perpetual",
    audience: "进阶",
    defaultParameters: { macd_fast: 12, macd_slow: 26, macd_signal: 9 },
  },
  {
    id: "bollinger_mean_reversion",
    label: "布林带均值回归策略",
    summary: "价格偏离带宽后回归中轴时离场。",
    market: "perpetual",
    audience: "进阶",
    defaultParameters: { bb_length: 20, bb_deviation: 2 },
  },
  {
    id: "breakout_trend",
    label: "Breakout 突破策略",
    summary: "突破前高/前低后顺势参与，适合扩张行情。",
    market: "perpetual",
    audience: "进阶",
    defaultParameters: { breakout_lookback: 20, volume_spike: 1.5 },
  },
  {
    id: "vwap_reversion",
    label: "VWAP 回归策略",
    summary: "围绕 VWAP 偏离与回归做日内均值回归。",
    market: "perpetual",
    audience: "进阶",
    defaultParameters: { deviation_threshold: 1.2, rsi_length: 14 },
  },
  {
    id: "supertrend_follow",
    label: "Supertrend 趋势策略",
    summary: "用 Supertrend 判断主趋势并在趋势切换时退出。",
    market: "perpetual",
    audience: "新手",
    defaultParameters: { atr_length: 10, multiplier: 3 },
  },
  {
    id: "multi_factor_confirmation",
    label: "多指标确认模板",
    summary: "EMA + RSI + 成交量联合确认，减少噪声信号。",
    market: "perpetual",
    audience: "进阶",
    defaultParameters: { ema_fast: 21, ema_slow: 55, rsi_length: 14, volume_ma: 20 },
  },
];

export const STRATEGY_INDICATOR_CATEGORIES: StrategyIndicatorCategory[] = [
  { id: "trend", label: "趋势类", indicators: ["SMA", "EMA", "WMA", "VWMA", "HMA", "MACD", "Supertrend", "Ichimoku", "ADX", "Parabolic SAR"] },
  { id: "momentum", label: "动量 / 震荡类", indicators: ["RSI", "Stochastic", "Stoch RSI", "CCI", "Williams %R", "ROC", "Momentum", "TRIX"] },
  { id: "volatility", label: "波动率类", indicators: ["Bollinger Bands", "ATR", "Keltner Channel", "Donchian Channel", "Historical Volatility"] },
  { id: "volume", label: "成交量类", indicators: ["Volume MA", "OBV", "VWAP", "MFI", "CMF", "Volume Spike"] },
  { id: "structure", label: "价格结构类", indicators: ["Breakout High/Low", "Pivot High/Low", "Support / Resistance", "Previous High/Low", "Opening Range Breakout"] },
  { id: "filters", label: "市场过滤类", indicators: ["Trend Filter", "Time Window Filter", "Funding Bias Filter", "Open Interest Bias Filter", "Session Filter"] },
];
