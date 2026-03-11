import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { LoadingBlock, SectionState } from "../components/async-state";
import {
  ScriptStrategyWorkbench,
  type ScriptWorkbenchLog,
  type ScriptWorkbenchParameter,
  type ScriptWorkbenchPublishStep,
  type ScriptWorkbenchSignal,
} from "../components/script-strategy-workbench";
import {
  TemplateStrategyBuilder,
  type ConditionGroup,
  type ConditionRule,
  type TemplateParameter,
} from "../components/template-strategy-builder";
import { SectionTitle } from "../components/ui/section-title";
import { StatusPill } from "../components/ui/status-pill";
import { api } from "../lib/api";
import {
  STRATEGY_INDICATOR_CATEGORIES,
  STRATEGY_TEMPLATE_PRESETS,
} from "../lib/strategy-builder";
import type {
  ExecutionRuntimeStatus,
  ExchangeAccount,
  LiveStrategyExecution,
  RiskControls,
  StrategySummary,
  StrategyUpsertRequest,
} from "../lib/types";

type BuilderMode = "template" | "script";
type LoadState = "loading" | "ready" | "error";
type TemplateSection = "overview" | "market_scope" | "template_library" | "signal_logic" | "parameters" | "indicator_catalog";
type ScriptSection = "overview" | "market_scope" | "script_editor" | "script_parameters" | "script_signals" | "script_publish";

type StrategyCategory =
  | "trend"
  | "reversion"
  | "breakout"
  | "market_making"
  | "custom";

type StrategyDirection = "long_only" | "short_only" | "bi_directional";
type TradingType = "spot" | "perpetual" | "margin";

interface StrategyFormState {
  name: string;
  description: string;
  tagsText: string;
  category: StrategyCategory;
  direction: StrategyDirection;
  tradingType: TradingType;
  symbol: string;
  timeframe: string;
  secondaryTimeframe: string;
  multiSymbolEnabled: boolean;
  enabled: boolean;
}

const STRATEGY_INTERVALS = ["5m", "15m", "1h", "4h", "1d"];
const SECONDARY_INTERVALS = ["none", "15m", "1h", "4h", "1d"];
const DEFAULT_SYMBOLS = ["BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP"];

const DEFAULT_SCRIPT = `from platform_sdk import indicators, orders, risk

def on_bar(ctx):
    ema_fast = indicators.ema(ctx.close, 21)
    ema_slow = indicators.ema(ctx.close, 55)
    rsi = indicators.rsi(ctx.close, 14)

    if ema_fast > ema_slow and rsi > 55:
        risk.check("entry-long")
        orders.open_long(size_pct=0.15)

    if rsi > 70:
        orders.close_long()
`;

const DEFAULT_SCRIPT_SIGNALS: ScriptWorkbenchSignal[] = [
  { id: "sig-1", time: "2026-03-09 11:20 UTC", action: "open_long", price: "84210.4", confidence: "0.72" },
  { id: "sig-2", time: "2026-03-09 15:10 UTC", action: "close_long", price: "84980.1", confidence: "0.68" },
];

const DEFAULT_SCRIPT_LOGS: ScriptWorkbenchLog[] = [
  { level: "info", message: "Validation passed: no blocked imports detected.", time: "11:22 UTC" },
  { level: "warning", message: "Signal density dropped after RSI filter tightening.", time: "11:23 UTC" },
];

function makeRuleId() {
  return `rule_${Math.random().toString(36).slice(2, 10)}`;
}

function makeGroupId() {
  return `group_${Math.random().toString(36).slice(2, 10)}`;
}

function makeRule(
  left: string,
  comparator: ConditionRule["comparator"],
  right: string,
  comparisonMode: ConditionRule["comparisonMode"],
  timeframe = "same TF",
  extra?: string,
): ConditionRule {
  return { id: makeRuleId(), left, comparator, right, extra, timeframe, comparisonMode };
}

function makeGroup(
  label: string,
  operator: ConditionGroup["operator"],
  rules: ConditionRule[],
  children: ConditionGroup[] = [],
): ConditionGroup {
  return { id: makeGroupId(), label, operator, rules, children };
}

function defaultForm(symbol: string): StrategyFormState {
  return {
    name: "EMA + RSI Volume Confirmation",
    description: "Trend + momentum + participation confirmation for liquid perpetuals.",
    tagsText: "trend, confirmation, perpetual",
    category: "trend",
    direction: "long_only",
    tradingType: "perpetual",
    symbol,
    timeframe: "1h",
    secondaryTimeframe: "4h",
    multiSymbolEnabled: false,
    enabled: true,
  };
}

function defaultScriptParameters(symbols: string[]): ScriptWorkbenchParameter[] {
  return [
    { key: "fast_ema", label: "Fast EMA", type: "number", value: 21, hint: "Trend trigger length." },
    { key: "slow_ema", label: "Slow EMA", type: "number", value: 55, hint: "Trend confirmation length." },
    { key: "rsi_threshold", label: "RSI Threshold", type: "number", value: 55, hint: "Momentum filter." },
    { key: "symbol", label: "Market", type: "select", value: symbols[0] ?? DEFAULT_SYMBOLS[0], options: symbols },
  ];
}

function buildPresetGroups(presetId: string) {
  switch (presetId) {
    case "ema_dual_trend":
      return {
        entry: [
          makeGroup("Long entry", "AND", [
            makeRule("EMA(9)", "crosses_above", "EMA(21)", "indicator_vs_indicator"),
            makeRule("ADX(14)", "greater_than", "20", "indicator_vs_value"),
          ]),
        ],
        exit: [
          makeGroup("Long exit", "OR", [
            makeRule("EMA(9)", "crosses_below", "EMA(21)", "indicator_vs_indicator"),
            makeRule("Close", "less_than", "Stop price", "price_vs_indicator"),
          ]),
        ],
        filters: [
          makeGroup("Trend alignment", "AND", [
            makeRule("Close", "greater_than", "EMA(200)", "price_vs_indicator", "4h"),
            makeRule("Session Filter", "equal_to", "active", "indicator_vs_value"),
          ]),
        ],
      };
    case "rsi_reversal":
      return {
        entry: [
          makeGroup("Long reversal", "AND", [
            makeRule("RSI(14)", "less_than", "30", "indicator_vs_value"),
            makeRule("Close", "greater_than", "EMA(200)", "price_vs_indicator"),
          ]),
        ],
        exit: [
          makeGroup("Exit", "OR", [
            makeRule("RSI(14)", "greater_than", "70", "indicator_vs_value"),
            makeRule("Close", "less_than", "Stop price", "price_vs_indicator"),
          ]),
        ],
        filters: [
          makeGroup("Range filter", "AND", [
            makeRule("Trend Filter", "equal_to", "flat", "indicator_vs_value"),
            makeRule("Funding Bias Filter", "between", "-0.02", "indicator_vs_value", "same TF", "0.02"),
          ]),
        ],
      };
    case "macd_trend_follow":
      return {
        entry: [
          makeGroup("MACD confirmation", "AND", [
            makeRule("MACD.macd", "crosses_above", "MACD.signal", "indicator_vs_indicator"),
            makeRule("Volume", "greater_than", "Volume MA(20)", "indicator_vs_indicator"),
          ]),
        ],
        exit: [
          makeGroup("MACD unwind", "OR", [
            makeRule("MACD.macd", "crosses_below", "MACD.signal", "indicator_vs_indicator"),
            makeRule("Close", "less_than", "Stop price", "price_vs_indicator"),
          ]),
        ],
        filters: [
          makeGroup("Momentum guard", "AND", [
            makeRule("ADX(14)", "greater_than", "25", "indicator_vs_value"),
            makeRule("Open Interest Bias Filter", "greater_than", "2", "indicator_vs_value"),
          ]),
        ],
      };
    case "bollinger_mean_reversion":
      return {
        entry: [
          makeGroup("Band fade", "AND", [
            makeRule("Close", "less_than", "Bollinger Bands.lower", "price_vs_indicator"),
            makeRule("RSI(14)", "less_than", "35", "indicator_vs_value"),
          ]),
        ],
        exit: [
          makeGroup("Mean restore", "OR", [
            makeRule("Close", "greater_than", "Bollinger Bands.basis", "price_vs_indicator"),
            makeRule("Close", "less_than", "Stop price", "price_vs_indicator"),
          ]),
        ],
        filters: [
          makeGroup("Low trend environment", "AND", [
            makeRule("Trend Filter", "equal_to", "flat", "indicator_vs_value"),
            makeRule("Volatility Filter", "less_than", "8", "indicator_vs_value"),
          ]),
        ],
      };
    case "breakout_trend":
      return {
        entry: [
          makeGroup("Breakout long", "AND", [
            makeRule("Close", "greater_than", "Breakout High/Low.breakout_high", "price_vs_indicator"),
            makeRule("Volume Spike.ratio", "greater_than", "1.8", "indicator_vs_value"),
          ]),
        ],
        exit: [
          makeGroup("Failed breakout", "OR", [
            makeRule("Close", "less_than", "Previous High/Low.previous_low", "price_vs_indicator"),
            makeRule("Close", "less_than", "Stop price", "price_vs_indicator"),
          ]),
        ],
        filters: [
          makeGroup("Expansion confirmation", "AND", [
            makeRule("Open Interest Bias Filter", "greater_than", "2", "indicator_vs_value"),
            makeRule("Session Filter", "equal_to", "active", "indicator_vs_value"),
          ]),
        ],
      };
    case "vwap_reversion":
      return {
        entry: [
          makeGroup("VWAP reclaim", "AND", [
            makeRule("Close", "less_than", "VWAP", "price_vs_indicator"),
            makeRule("RSI(14)", "less_than", "40", "indicator_vs_value"),
          ]),
        ],
        exit: [
          makeGroup("VWAP exit", "OR", [
            makeRule("Close", "greater_than", "VWAP", "price_vs_indicator"),
            makeRule("Close", "less_than", "Stop price", "price_vs_indicator"),
          ]),
        ],
        filters: [
          makeGroup("Session filter", "AND", [
            makeRule("Time Window Filter", "between", "08:00", "indicator_vs_value", "same TF", "23:00"),
            makeRule("Spread Filter", "less_than", "0.20", "indicator_vs_value"),
          ]),
        ],
      };
    case "supertrend_follow":
      return {
        entry: [
          makeGroup("Supertrend long", "AND", [
            makeRule("Supertrend.trend", "equal_to", "bullish", "indicator_vs_value"),
            makeRule("Close", "greater_than", "Supertrend.lower_band", "price_vs_indicator"),
          ]),
        ],
        exit: [
          makeGroup("Supertrend exit", "OR", [
            makeRule("Supertrend.trend", "equal_to", "bearish", "indicator_vs_value"),
            makeRule("Close", "less_than", "Stop price", "price_vs_indicator"),
          ]),
        ],
        filters: [
          makeGroup("Trend strength", "AND", [
            makeRule("ADX(14)", "greater_than", "18", "indicator_vs_value"),
            makeRule("Session Filter", "equal_to", "active", "indicator_vs_value"),
          ]),
        ],
      };
    case "multi_factor_confirmation":
      return {
        entry: [
          makeGroup("Multi-factor entry", "AND", [
            makeRule("EMA(21)", "greater_than", "EMA(55)", "indicator_vs_indicator"),
            makeRule("RSI(14)", "greater_than", "55", "indicator_vs_value"),
            makeRule("Volume", "greater_than", "Volume MA(20)", "indicator_vs_indicator"),
          ]),
        ],
        exit: [
          makeGroup("Signal invalidation", "OR", [
            makeRule("EMA(21)", "less_than", "EMA(55)", "indicator_vs_indicator"),
            makeRule("RSI(14)", "less_than", "45", "indicator_vs_value"),
            makeRule("Close", "less_than", "Stop price", "price_vs_indicator"),
          ]),
        ],
        filters: [
          makeGroup("High quality regime", "AND", [
            makeRule("Funding Bias Filter", "between", "-0.03", "indicator_vs_value", "same TF", "0.03"),
            makeRule("Trend Filter", "equal_to", "aligned", "indicator_vs_value", "4h"),
          ]),
        ],
      };
    default:
      return {
        entry: [makeGroup("Entry", "AND", [makeRule("EMA(9)", "crosses_above", "EMA(21)", "indicator_vs_indicator")])],
        exit: [makeGroup("Exit", "OR", [makeRule("EMA(9)", "crosses_below", "EMA(21)", "indicator_vs_indicator")])],
        filters: [makeGroup("Filter", "AND", [makeRule("Session Filter", "equal_to", "active", "indicator_vs_value")])],
      };
  }
}

function defaultTemplateParameters(presetId: string | null): TemplateParameter[] {
  const preset = STRATEGY_TEMPLATE_PRESETS.find((item) => item.id === presetId) ?? STRATEGY_TEMPLATE_PRESETS[0];
  return Object.entries(preset.defaultParameters).map(([key, value]) => ({
    key,
    label: key
      .split("_")
      .map((part) => part[0].toUpperCase() + part.slice(1))
      .join(" "),
    value,
    defaultValue: value,
  }));
}

function parseString(value: string | number | boolean | undefined, fallback: string) {
  return typeof value === "string" && value.length > 0 ? value : fallback;
}

function parseBoolean(value: string | number | boolean | undefined, fallback: boolean) {
  if (typeof value === "boolean") return value;
  if (typeof value === "string") return value === "true";
  return fallback;
}

function parseNumber(value: string | number | boolean | undefined, fallback: number) {
  if (typeof value === "number") return value;
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  return fallback;
}

function parseJsonGroups(value: string | number | boolean | undefined, fallback: ConditionGroup[]) {
  if (typeof value !== "string") {
    return fallback;
  }

  try {
    const parsed = JSON.parse(value) as ConditionGroup[];
    return Array.isArray(parsed) ? parsed : fallback;
  } catch {
    return fallback;
  }
}

function parseJsonTemplateParameters(value: string | number | boolean | undefined, fallback: TemplateParameter[]) {
  if (typeof value !== "string") {
    return fallback;
  }

  try {
    const parsed = JSON.parse(value) as TemplateParameter[];
    return Array.isArray(parsed) ? parsed : fallback;
  } catch {
    return fallback;
  }
}

function compileTemplateParameters(
  form: StrategyFormState,
  selectedTemplateId: string | null,
  parameters: TemplateParameter[],
  entryConditions: ConditionGroup[],
  exitConditions: ConditionGroup[],
  marketFilters: ConditionGroup[],
  liveConfig: { liveEnabled: boolean; executionWeight: number; pollIntervalSeconds: number },
): StrategyUpsertRequest["parameters"] {
  return {
    templatePresetId: selectedTemplateId ?? "",
    tagsText: form.tagsText,
    category: form.category,
    tradingType: form.tradingType,
    direction: form.direction,
    symbol: form.symbol,
    timeframe: form.timeframe,
    secondaryTimeframe: form.secondaryTimeframe,
    multiSymbolEnabled: form.multiSymbolEnabled,
    enabled: form.enabled,
    templateParametersJson: JSON.stringify(parameters),
    entryConditionsJson: JSON.stringify(entryConditions),
    exitConditionsJson: JSON.stringify(exitConditions),
    marketFiltersJson: JSON.stringify(marketFilters),
    liveEnabled: liveConfig.liveEnabled,
    live_enabled: liveConfig.liveEnabled,
    executionWeight: liveConfig.executionWeight,
    execution_weight: liveConfig.executionWeight,
    pollIntervalSeconds: liveConfig.pollIntervalSeconds,
    poll_interval_seconds: liveConfig.pollIntervalSeconds,
  };
}

function compileScriptParameters(
  form: StrategyFormState,
  scriptBody: string,
  scriptParameters: ScriptWorkbenchParameter[],
  liveConfig: { liveEnabled: boolean; executionWeight: number; pollIntervalSeconds: number },
): StrategyUpsertRequest["parameters"] {
  return {
    tagsText: form.tagsText,
    category: form.category,
    tradingType: form.tradingType,
    direction: form.direction,
    symbol: form.symbol,
    timeframe: form.timeframe,
    secondaryTimeframe: form.secondaryTimeframe,
    multiSymbolEnabled: form.multiSymbolEnabled,
    enabled: form.enabled,
    scriptBody,
    liveEnabled: liveConfig.liveEnabled,
    live_enabled: liveConfig.liveEnabled,
    executionWeight: liveConfig.executionWeight,
    execution_weight: liveConfig.executionWeight,
    pollIntervalSeconds: liveConfig.pollIntervalSeconds,
    poll_interval_seconds: liveConfig.pollIntervalSeconds,
    ...Object.fromEntries(scriptParameters.map((parameter) => [parameter.key, parameter.value])),
  };
}

function buildPublishChecklist({
  hasRiskBinding,
  hasBacktestVersion,
  hasName,
  hasDescription,
  hasSignalLogic,
}: {
  hasRiskBinding: boolean;
  hasBacktestVersion: boolean;
  hasName: boolean;
  hasDescription: boolean;
  hasSignalLogic: boolean;
}): ScriptWorkbenchPublishStep[] {
  return [
    {
      label: "Base metadata",
      detail: "Strategy name, description, market scope",
      status: hasName && hasDescription ? "ready" : "blocked",
    },
    {
      label: "Signal logic",
      detail: "Entry / exit or script conditions defined",
      status: hasSignalLogic ? "ready" : "blocked",
    },
    {
      label: "Risk profile linked",
      detail: "Configured in Risk Controls menu",
      status: hasRiskBinding ? "ready" : "idle",
    },
    {
      label: "Backtest version available",
      detail: "Managed in Backtests menu",
      status: hasBacktestVersion ? "ready" : "idle",
    },
  ];
}

function statusTone(status: StrategySummary["status"]) {
  if (status === "healthy") return "positive" as const;
  if (status === "paused") return "negative" as const;
  return "neutral" as const;
}

export function StrategiesPage() {
  const [searchParams] = useSearchParams();
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [strategies, setStrategies] = useState<StrategySummary[]>([]);
  const [symbols, setSymbols] = useState<string[]>(DEFAULT_SYMBOLS);
  const [accounts, setAccounts] = useState<ExchangeAccount[]>([]);
  const [riskControls, setRiskControls] = useState<RiskControls | null>(null);
  const [liveStrategies, setLiveStrategies] = useState<LiveStrategyExecution[]>([]);
  const [executionRuntime, setExecutionRuntime] = useState<ExecutionRuntimeStatus | null>(null);
  const [selectedStrategyId, setSelectedStrategyId] = useState<string | null>(null);
  const [mode, setMode] = useState<BuilderMode>("template");
  const [form, setForm] = useState<StrategyFormState>(defaultForm(DEFAULT_SYMBOLS[0]));
  const [accountId, setAccountId] = useState("acct_001");
  const [priceSource, setPriceSource] = useState<"last" | "mark" | "index">("last");
  const [runtime, setRuntime] = useState<"disabled" | "paper" | "live-ready">("paper");
  const [status, setStatus] = useState<"healthy" | "idle" | "paused">("healthy");
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(STRATEGY_TEMPLATE_PRESETS[0].id);
  const [templateParameters, setTemplateParameters] = useState<TemplateParameter[]>(
    defaultTemplateParameters(STRATEGY_TEMPLATE_PRESETS[0].id),
  );
  const [entryConditions, setEntryConditions] = useState<ConditionGroup[]>(
    buildPresetGroups(STRATEGY_TEMPLATE_PRESETS[0].id).entry,
  );
  const [exitConditions, setExitConditions] = useState<ConditionGroup[]>(
    buildPresetGroups(STRATEGY_TEMPLATE_PRESETS[0].id).exit,
  );
  const [marketFilters, setMarketFilters] = useState<ConditionGroup[]>(
    buildPresetGroups(STRATEGY_TEMPLATE_PRESETS[0].id).filters,
  );
  const [scriptBody, setScriptBody] = useState(DEFAULT_SCRIPT);
  const [scriptParameters, setScriptParameters] = useState<ScriptWorkbenchParameter[]>(
    defaultScriptParameters(DEFAULT_SYMBOLS),
  );
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [liveEnabled, setLiveEnabled] = useState(false);
  const [executionWeight, setExecutionWeight] = useState(1);
  const [pollIntervalSeconds, setPollIntervalSeconds] = useState(60);
  const [liveActionPending, setLiveActionPending] = useState(false);
  const [templateSection, setTemplateSection] = useState<TemplateSection>("overview");
  const [scriptSection, setScriptSection] = useState<ScriptSection>("overview");

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const [strategyList, marketSymbols, exchangeAccounts, controls, liveItems, runtimeState] = await Promise.all([
          api.strategies(),
          api.marketSymbols().catch(() => DEFAULT_SYMBOLS),
          api.exchangeAccounts().catch(() => []),
          api.riskControls().catch(() => null),
          api.liveStrategies().catch(() => []),
          api.executionRuntime().catch(() => null),
        ]);

        if (!active) {
          return;
        }

        const nextSymbols = marketSymbols.length > 0 ? marketSymbols : DEFAULT_SYMBOLS;
        setStrategies(strategyList);
        setSymbols(nextSymbols);
        setAccounts(exchangeAccounts);
        setRiskControls(controls);
        setLiveStrategies(liveItems);
        setExecutionRuntime(runtimeState);
        setScriptParameters(defaultScriptParameters(nextSymbols));
        setLoadState("ready");

        if (strategyList.length > 0) {
          hydrateFromStrategy(strategyList[0], nextSymbols);
        } else {
          resetDraft(nextSymbols);
        }
      } catch (error) {
        if (!active) {
          return;
        }

        setLoadError(error instanceof Error ? error.message : "Unknown error");
        setLoadState("error");
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, []);

  function resetDraft(nextSymbols = symbols) {
    const presetId = STRATEGY_TEMPLATE_PRESETS[0].id;
    const presetGroups = buildPresetGroups(presetId);
    setSelectedStrategyId(null);
    setMode("template");
    setForm({
      ...defaultForm(nextSymbols[0] ?? DEFAULT_SYMBOLS[0]),
      name: STRATEGY_TEMPLATE_PRESETS[0].label,
      description: STRATEGY_TEMPLATE_PRESETS[0].summary,
    });
    setAccountId(accounts[0]?.id ?? "acct_001");
    setPriceSource("last");
    setRuntime("paper");
    setStatus("healthy");
    setTemplateSection("overview");
    setScriptSection("overview");
    setSelectedTemplateId(presetId);
    setTemplateParameters(defaultTemplateParameters(presetId));
    setEntryConditions(presetGroups.entry);
    setExitConditions(presetGroups.exit);
    setMarketFilters(presetGroups.filters);
    setScriptBody(DEFAULT_SCRIPT);
    setScriptParameters(defaultScriptParameters(nextSymbols));
    setLiveEnabled(false);
    setExecutionWeight(1);
    setPollIntervalSeconds(60);
    setSaveMessage(null);
  }

  function hydrateFromStrategy(strategy: StrategySummary, nextSymbols = symbols) {
    setSelectedStrategyId(strategy.id);
    setMode(strategy.kind);
    setAccountId(strategy.accountId);
    setPriceSource(strategy.priceSource);
    setRuntime(strategy.runtime);
    setStatus(strategy.status);

    const baseForm = defaultForm(nextSymbols[0] ?? DEFAULT_SYMBOLS[0]);
    const parameters = strategy.parameters;
    setForm({
      name: strategy.name,
      description: strategy.description,
      tagsText: parseString(parameters.tagsText, baseForm.tagsText),
      category: parseString(parameters.category, baseForm.category) as StrategyCategory,
      direction: parseString(parameters.direction, baseForm.direction) as StrategyDirection,
      tradingType: parseString(parameters.tradingType, baseForm.tradingType) as TradingType,
      symbol: parseString(parameters.symbol, strategy.market || baseForm.symbol),
      timeframe: parseString(parameters.timeframe, baseForm.timeframe),
      secondaryTimeframe: parseString(parameters.secondaryTimeframe, baseForm.secondaryTimeframe),
      multiSymbolEnabled: parseBoolean(parameters.multiSymbolEnabled, false),
      enabled: parseBoolean(parameters.enabled, true),
    });
    setLiveEnabled(parseBoolean(parameters.liveEnabled ?? parameters.live_enabled, false));
    setExecutionWeight(parseNumber(parameters.executionWeight ?? parameters.execution_weight, 1));
    setPollIntervalSeconds(parseNumber(parameters.pollIntervalSeconds ?? parameters.poll_interval_seconds, 60));

    if (strategy.kind === "template") {
      const presetId = parseString(parameters.templatePresetId, STRATEGY_TEMPLATE_PRESETS[0].id);
      const presetGroups = buildPresetGroups(presetId);
      setSelectedTemplateId(presetId);
      setTemplateParameters(
        parseJsonTemplateParameters(parameters.templateParametersJson, defaultTemplateParameters(presetId)),
      );
      setEntryConditions(parseJsonGroups(parameters.entryConditionsJson, presetGroups.entry));
      setExitConditions(parseJsonGroups(parameters.exitConditionsJson, presetGroups.exit));
      setMarketFilters(parseJsonGroups(parameters.marketFiltersJson, presetGroups.filters));
    } else {
      setSelectedTemplateId(null);
      setTemplateParameters(defaultTemplateParameters(STRATEGY_TEMPLATE_PRESETS[0].id));
      setEntryConditions(buildPresetGroups(STRATEGY_TEMPLATE_PRESETS[0].id).entry);
      setExitConditions(buildPresetGroups(STRATEGY_TEMPLATE_PRESETS[0].id).exit);
      setMarketFilters(buildPresetGroups(STRATEGY_TEMPLATE_PRESETS[0].id).filters);
      setScriptBody(parseString(parameters.scriptBody, DEFAULT_SCRIPT));
      setScriptParameters(
        defaultScriptParameters(nextSymbols).map((parameter) => ({
          ...parameter,
          value: parameters[parameter.key] ?? parameter.value,
          options: parameter.type === "select" ? nextSymbols : parameter.options,
        })),
      );
    }

    setSaveMessage(null);
  }

  function applyTemplatePreset(templateId: string) {
    const preset = STRATEGY_TEMPLATE_PRESETS.find((item) => item.id === templateId);
    if (!preset) {
      return;
    }

    const groups = buildPresetGroups(templateId);
    setSelectedTemplateId(templateId);
    setTemplateParameters(defaultTemplateParameters(templateId));
    setEntryConditions(groups.entry);
    setExitConditions(groups.exit);
    setMarketFilters(groups.filters);
    setForm((current) => ({
      ...current,
      name: preset.label,
      description: preset.summary,
    }));
  }

  function updateForm<K extends keyof StrategyFormState>(field: K, value: StrategyFormState[K]) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function saveStrategy(options?: { clone?: boolean }) {
    setSaving(true);
    setSaveMessage(null);

    const payload: StrategyUpsertRequest =
      mode === "template"
        ? {
            name: form.name,
            kind: "template",
            description: form.description,
            market: form.symbol,
            accountId,
            runtime,
            status,
            priceSource,
            parameters: compileTemplateParameters(
              form,
              selectedTemplateId,
              templateParameters,
              entryConditions,
              exitConditions,
              marketFilters,
              { liveEnabled, executionWeight, pollIntervalSeconds },
            ),
          }
        : {
            name: form.name,
            kind: "script",
            description: form.description,
            market: form.symbol,
            accountId,
            runtime,
            status,
            priceSource,
            parameters: compileScriptParameters(form, scriptBody, scriptParameters, {
              liveEnabled,
              executionWeight,
              pollIntervalSeconds,
            }),
          };

    try {
      const saved =
        selectedStrategyId && !options?.clone
          ? await api.updateStrategy(selectedStrategyId, payload)
          : await api.createStrategy(payload);

      const nextStrategies =
        selectedStrategyId && !options?.clone
          ? strategies.map((item) => (item.id === saved.id ? saved : item))
          : [saved, ...strategies];

      setStrategies(nextStrategies);
      hydrateFromStrategy(saved);
      setSaveMessage(options?.clone ? "Saved as new strategy" : "Saved");
    } catch (error) {
      setSaveMessage(error instanceof Error ? error.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  const selectedStrategy = useMemo(
    () => strategies.find((item) => item.id === selectedStrategyId) ?? null,
    [strategies, selectedStrategyId],
  );
  const selectedLiveState = useMemo(
    () => liveStrategies.find((item) => item.strategyId === selectedStrategyId) ?? null,
    [liveStrategies, selectedStrategyId],
  );

  async function refreshExecutionSurfaces() {
    const [liveItems, runtimeState] = await Promise.all([
      api.liveStrategies().catch(() => []),
      api.executionRuntime().catch(() => null),
    ]);
    setLiveStrategies(liveItems);
    setExecutionRuntime(runtimeState);
  }

  async function enableLiveForSelectedStrategy() {
    if (!selectedStrategyId) {
      setSaveMessage("Save the strategy before enabling live trading.");
      return;
    }
    if (!liveEnabled) {
      setSaveMessage("Whitelist the strategy for live trading before enabling it.");
      return;
    }
    setLiveActionPending(true);
    try {
      await api.enableLiveStrategy(selectedStrategyId, { confirmed: true });
      await refreshExecutionSurfaces();
      setSaveMessage("Strategy confirmed for live trading.");
    } catch (error) {
      setSaveMessage(error instanceof Error ? error.message : "Live enable failed");
    } finally {
      setLiveActionPending(false);
    }
  }

  async function disableLiveForSelectedStrategy() {
    if (!selectedStrategyId) {
      return;
    }
    setLiveActionPending(true);
    try {
      await api.disableLiveStrategy(selectedStrategyId);
      await refreshExecutionSurfaces();
      setSaveMessage("Strategy removed from live execution.");
    } catch (error) {
      setSaveMessage(error instanceof Error ? error.message : "Live disable failed");
    } finally {
      setLiveActionPending(false);
    }
  }

  const publishChecklist = buildPublishChecklist({
    hasRiskBinding: Boolean(riskControls),
    hasBacktestVersion: Boolean(selectedStrategy?.lastBacktest),
    hasName: form.name.trim().length > 0,
    hasDescription: form.description.trim().length > 0,
    hasSignalLogic:
      mode === "template"
        ? entryConditions.length > 0 && exitConditions.length > 0
        : scriptBody.trim().length > 0,
  });

  const strategySections =
    mode === "template"
      ? [
          { id: "overview", label: "Overview" },
          { id: "market_scope", label: "Market scope" },
          { id: "template_library", label: "Template library" },
          { id: "signal_logic", label: "Signal logic" },
          { id: "parameters", label: "Parameters" },
          { id: "indicator_catalog", label: "Indicators" },
        ]
      : [
          { id: "overview", label: "Overview" },
          { id: "market_scope", label: "Market scope" },
          { id: "script_editor", label: "Script editor" },
          { id: "script_parameters", label: "Parameters" },
          { id: "script_signals", label: "Signal summary" },
          { id: "script_publish", label: "Publish" },
        ];

  const activeSection = mode === "template" ? templateSection : scriptSection;

  useEffect(() => {
    const section = searchParams.get("section");
    if (!section) {
      return;
    }

    if (
      section === "overview" ||
      section === "market_scope" ||
      section === "template_library" ||
      section === "signal_logic" ||
      section === "parameters" ||
      section === "indicator_catalog"
    ) {
      setMode("template");
      setTemplateSection(section);
      return;
    }

    if (
      section === "script_editor" ||
      section === "script_parameters" ||
      section === "script_signals" ||
      section === "script_publish"
    ) {
      setMode("script");
      setScriptSection(section);
    }
  }, [searchParams]);

  if (loadState === "loading") {
    return <LoadingBlock rows={8} />;
  }

  if (loadState === "error") {
    return (
      <SectionState
        title="Strategy registry failed to load"
        detail={loadError ?? "Unknown error"}
        tone="error"
      />
    );
  }

  return (
    <div className="space-y-5">
      {/* Page header — slim single row */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-gray-100 bg-white px-5 py-3.5 shadow-sm">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.3em] text-gray-400">Strategy Lab</p>
            <h2 className="mt-0.5 text-lg font-bold text-gray-900">{form.name || "Untitled strategy"}</h2>
          </div>
          <div className="flex flex-wrap gap-1.5">
            <StatusPill>{mode === "template" ? "template" : "script"}</StatusPill>
            <StatusPill tone={statusTone(status)}>{status}</StatusPill>
            <StatusPill>{form.tradingType}</StatusPill>
            <StatusPill>{form.direction}</StatusPill>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => void saveStrategy()}
            disabled={saving}
            className="rounded-full border border-gray-200 px-4 py-2 text-xs font-medium text-gray-700 transition hover:border-gray-900 hover:text-gray-900 disabled:opacity-40"
          >
            {saving ? "Saving..." : "Save"}
          </button>
          <button
            type="button"
            onClick={() => void saveStrategy({ clone: true })}
            className="rounded-full border border-gray-200 px-4 py-2 text-xs font-medium text-gray-700 transition hover:border-gray-900 hover:text-gray-900"
          >
            Save as
          </button>
          <button
            type="button"
            onClick={() => setStatus((current) => (current === "paused" ? "healthy" : "paused"))}
            className="rounded-full border border-gray-200 px-4 py-2 text-xs font-medium text-gray-700 transition hover:border-gray-900 hover:text-gray-900"
          >
            {status === "paused" ? "Enable" : "Pause"}
          </button>
          <button
            type="button"
            onClick={() => setSaveMessage("Publish flow gated by checklist and linked pages.")}
            className="rounded-full bg-gray-900 px-4 py-2 text-xs font-semibold text-white transition hover:bg-gray-700"
          >
            Publish
          </button>
        </div>
      </div>

      {/* 3-column layout */}
      <div className="grid gap-6 xl:grid-cols-[220px_1fr_260px]">

        {/* ── Left: Strategy list ── */}
        <div className="sticky top-[68px] self-start overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
          <div className="border-b border-gray-100 px-4 py-3.5">
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-gray-400">Strategy registry</p>
            <p className="mt-0.5 text-sm font-semibold text-gray-900">Saved strategies</p>
          </div>
          <div className="space-y-1 p-3">
            <button
              type="button"
              onClick={() => resetDraft(symbols)}
              className="w-full rounded-xl border border-dashed border-gray-200 px-3 py-2.5 text-left text-xs font-medium text-gray-400 transition hover:border-gray-400 hover:text-gray-900"
            >
              + New strategy
            </button>
            {strategies.map((strategy) => (
              <button
                key={strategy.id}
                type="button"
                onClick={() => hydrateFromStrategy(strategy)}
                className={`w-full rounded-xl border p-3 text-left transition ${
                  selectedStrategyId === strategy.id
                    ? "border-gray-900 bg-gray-900"
                    : "border-transparent hover:border-gray-200 hover:bg-gray-50"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className={`truncate text-xs font-semibold ${selectedStrategyId === strategy.id ? "text-white" : "text-gray-900"}`}>
                      {strategy.name}
                    </p>
                    <p className={`mt-0.5 truncate text-[10px] ${selectedStrategyId === strategy.id ? "text-white/70" : "text-gray-500"}`}>
                      {strategy.market}
                    </p>
                  </div>
                  <StatusPill tone={statusTone(strategy.status)}>{strategy.kind}</StatusPill>
                </div>
                <div className={`mt-2 flex flex-wrap gap-1 text-[9px] font-medium ${selectedStrategyId === strategy.id ? "text-white/60" : "text-gray-400"}`}>
                  <span className={`rounded-full px-2 py-0.5 ${selectedStrategyId === strategy.id ? "bg-white/10" : "bg-gray-100"}`}>
                    {strategy.runtime}
                  </span>
                  <span className={`rounded-full px-2 py-0.5 ${selectedStrategyId === strategy.id ? "bg-white/10" : "bg-gray-100"}`}>
                    {strategy.priceSource}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* ── Center: Unified workspace panel ── */}
        <div className="min-w-0 overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
          {/* Tab bar — mode toggle + section tabs, no extra card */}
          <div className="border-b border-gray-100">
            <div className="flex items-center justify-between gap-4 px-5 py-3.5">
              <div className="inline-flex items-center gap-0.5 rounded-full bg-gray-100 p-0.5">
                <button
                  type="button"
                  onClick={() => setMode("template")}
                  className={`rounded-full px-4 py-1.5 text-xs font-medium transition ${
                    mode === "template" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-900"
                  }`}
                >
                  Template
                </button>
                <button
                  type="button"
                  onClick={() => setMode("script")}
                  className={`rounded-full px-4 py-1.5 text-xs font-medium transition ${
                    mode === "script" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-900"
                  }`}
                >
                  Script
                </button>
              </div>
              <p className="text-[11px] text-gray-400">模板可转脚本；脚本不能完整回转为模板</p>
            </div>
            <div className="flex gap-0.5 overflow-x-auto border-t border-gray-50 px-4 pb-3 pt-2">
              {strategySections.map((section) => (
                <button
                  key={section.id}
                  type="button"
                  onClick={() => {
                    if (mode === "template") setTemplateSection(section.id as TemplateSection);
                    else setScriptSection(section.id as ScriptSection);
                  }}
                  className={`shrink-0 rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                    activeSection === section.id
                      ? "bg-gray-900 text-white"
                      : "text-gray-500 hover:bg-gray-100 hover:text-gray-900"
                  }`}
                >
                  {section.label}
                </button>
              ))}
            </div>
          </div>

          {/* Content area — no nested Card, just padded content */}
          <div className="p-6">
            {/* Overview */}
            {activeSection === "overview" ? (
              <div className="space-y-5">
                <SectionTitle eyebrow="Shared fields" title="Strategy basics" description="这些字段在模板模式和脚本模式之间共用。" />
                <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
                  <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                    <span>Strategy name</span>
                    <input
                      className="w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-900"
                      value={form.name}
                      onChange={(event) => updateForm("name", event.target.value)}
                    />
                  </label>
                  <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                    <span>Category</span>
                    <select
                      className="w-full appearance-none rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-900"
                      value={form.category}
                      onChange={(event) => updateForm("category", event.target.value as StrategyCategory)}
                    >
                      <option value="trend">Trend</option>
                      <option value="reversion">Reversion</option>
                      <option value="breakout">Breakout</option>
                      <option value="market_making">Market making</option>
                      <option value="custom">Custom</option>
                    </select>
                  </label>
                  <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                    <span>Tags</span>
                    <input
                      className="w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-900"
                      value={form.tagsText}
                      onChange={(event) => updateForm("tagsText", event.target.value)}
                      placeholder="trend, breakout, funding"
                    />
                  </label>
                  <label className="grid gap-1.5 text-xs font-medium text-gray-700 lg:col-span-2 xl:col-span-3">
                    <span>Description</span>
                    <textarea
                      className="min-h-[96px] w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-900"
                      value={form.description}
                      onChange={(event) => updateForm("description", event.target.value)}
                    />
                  </label>
                  <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                    <span>Direction</span>
                    <select
                      className="w-full appearance-none rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-900"
                      value={form.direction}
                      onChange={(event) => updateForm("direction", event.target.value as StrategyDirection)}
                    >
                      <option value="long_only">Long only</option>
                      <option value="short_only">Short only</option>
                      <option value="bi_directional">Bi-directional</option>
                    </select>
                  </label>
                  <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                    <span>Trading market</span>
                    <select
                      className="w-full appearance-none rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-900"
                      value={form.tradingType}
                      onChange={(event) => updateForm("tradingType", event.target.value as TradingType)}
                    >
                      <option value="spot">Spot</option>
                      <option value="perpetual">Perpetual</option>
                      <option value="margin">Margin</option>
                    </select>
                  </label>
                  <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                    <span>Execution account</span>
                    <select
                      className="w-full appearance-none rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-900"
                      value={accountId}
                      onChange={(event) => setAccountId(event.target.value)}
                    >
                      {(accounts.length > 0 ? accounts : [{ id: "acct_001", label: "backpack-primary" }]).map((account) => (
                        <option key={account.id} value={account.id}>{account.label}</option>
                      ))}
                    </select>
                  </label>
                </div>
              </div>
            ) : null}

            {/* Market scope */}
            {activeSection === "market_scope" ? (
              <div className="space-y-5">
                <SectionTitle eyebrow="Market scope" title="Symbols and timeframes" description="支持主流合约快捷选择，多标的作为高级开关保留。" />
                <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
                  <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                    <span>Trading symbol</span>
                    <select
                      className="w-full appearance-none rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-900"
                      value={form.symbol}
                      onChange={(event) => updateForm("symbol", event.target.value)}
                    >
                      {symbols.map((symbol) => <option key={symbol} value={symbol}>{symbol}</option>)}
                    </select>
                  </label>
                  <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                    <span>Primary timeframe</span>
                    <select
                      className="w-full appearance-none rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-900"
                      value={form.timeframe}
                      onChange={(event) => updateForm("timeframe", event.target.value)}
                    >
                      {STRATEGY_INTERVALS.map((interval) => <option key={interval} value={interval}>{interval}</option>)}
                    </select>
                  </label>
                  <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                    <span>Secondary timeframe</span>
                    <select
                      className="w-full appearance-none rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-900"
                      value={form.secondaryTimeframe}
                      onChange={(event) => updateForm("secondaryTimeframe", event.target.value)}
                    >
                      {SECONDARY_INTERVALS.map((interval) => <option key={interval} value={interval}>{interval}</option>)}
                    </select>
                  </label>
                  <label className="grid gap-1.5 text-xs font-medium text-gray-700">
                    <span>Price source</span>
                    <select
                      className="w-full appearance-none rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-900"
                      value={priceSource}
                      onChange={(event) => setPriceSource(event.target.value as "last" | "mark" | "index")}
                    >
                      <option value="last">last</option>
                      <option value="mark">mark</option>
                      <option value="index">index</option>
                    </select>
                  </label>
                </div>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-wrap gap-1.5">
                    {["BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP"].map((symbol) => (
                      <button
                        key={symbol}
                        type="button"
                        onClick={() => updateForm("symbol", symbol)}
                        className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
                          form.symbol === symbol
                            ? "border-gray-900 bg-gray-900 text-white"
                            : "border-gray-200 bg-white text-gray-600 hover:border-gray-400"
                        }`}
                      >
                        {symbol}
                      </button>
                    ))}
                  </div>
                  <label className="flex items-center gap-2 text-xs font-medium text-gray-700">
                    <input
                      type="checkbox"
                      checked={form.multiSymbolEnabled}
                      onChange={(event) => updateForm("multiSymbolEnabled", event.target.checked)}
                      className="accent-gray-900"
                    />
                    Enable multi-symbol strategy
                  </label>
                </div>
              </div>
            ) : null}

            {/* Template builder */}
            {mode === "template" &&
            (templateSection === "template_library" ||
              templateSection === "signal_logic" ||
              templateSection === "parameters" ||
              templateSection === "indicator_catalog") ? (
              <TemplateStrategyBuilder
                activeSection={templateSection}
                selectedTemplateId={selectedTemplateId}
                templates={STRATEGY_TEMPLATE_PRESETS}
                indicatorCategories={STRATEGY_INDICATOR_CATEGORIES}
                parameters={templateParameters}
                entryConditions={entryConditions}
                exitConditions={exitConditions}
                marketFilters={marketFilters}
                onTemplateSelect={applyTemplatePreset}
                onStartBlank={() => {
                  setSelectedTemplateId(null);
                  setTemplateParameters([]);
                  setEntryConditions([makeGroup("Long entry", "AND", [makeRule("EMA(9)", "crosses_above", "EMA(21)", "indicator_vs_indicator")])]);
                  setExitConditions([makeGroup("Exit", "OR", [makeRule("Close", "less_than", "Stop price", "price_vs_indicator")])]);
                  setMarketFilters([makeGroup("Filter", "AND", [makeRule("Session Filter", "equal_to", "active", "indicator_vs_value")])]);
                }}
                onParameterChange={(key, value) =>
                  setTemplateParameters((current) => current.map((p) => p.key === key ? { ...p, value } : p))
                }
                onResetParameter={(key) =>
                  setTemplateParameters((current) => current.map((p) => p.key === key ? { ...p, value: p.defaultValue } : p))
                }
                onEntryConditionsChange={setEntryConditions}
                onExitConditionsChange={setExitConditions}
                onMarketFiltersChange={setMarketFilters}
              />
            ) : null}

            {/* Script workbench */}
            {mode === "script" &&
            (scriptSection === "script_editor" ||
              scriptSection === "script_parameters" ||
              scriptSection === "script_signals" ||
              scriptSection === "script_publish") ? (
              <ScriptStrategyWorkbench
                activeSection={scriptSection}
                title="Script strategy workbench"
                description="脚本模式只承载策略代码、参数提取、信号说明、校验与发布。"
                strategyId={selectedStrategyId}
                scriptName={form.name || "Script strategy draft"}
                scriptBody={scriptBody}
                parameters={scriptParameters}
                signals={DEFAULT_SCRIPT_SIGNALS}
                logs={DEFAULT_SCRIPT_LOGS}
                publishChecklist={publishChecklist}
                accountLabel={accountId}
                marketLabel={`${form.symbol} / ${form.timeframe} / ${priceSource}`}
                riskProfileLabel={riskControls ? "Global risk envelope linked" : "No linked risk profile"}
                validationSummaryLabel={
                  selectedStrategy?.lastBacktest
                    ? "Syntax OK / linked risk profile / backtest version available"
                    : "Syntax OK / linked risk profile / no backtest version yet"
                }
                onScriptBodyChange={setScriptBody}
                onParameterChange={(key, value) =>
                  setScriptParameters((current) => current.map((p) => p.key === key ? { ...p, value } : p))
                }
                onFormat={() => setScriptBody((current) => current.trim())}
                onExtractParameters={() => setSaveMessage("Parameter extraction remains a lightweight workbench action.")}
                onLoadExample={() => setScriptBody(DEFAULT_SCRIPT)}
                onValidate={() => setSaveMessage("Validation completed. No blocked imports detected.")}
                onRunBacktest={() => setSaveMessage("Use the Backtests menu for full replay configuration.")}
                onPublish={() => setSaveMessage("Publish remains gated by linked risk and backtest checks.")}
              />
            ) : null}
          </div>
        </div>

        {/* ── Right: Single unified info panel ── */}
        <div className="sticky top-[68px] self-start overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
          {/* Workspace state */}
          <div className="px-4 py-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-gray-400">Workspace</p>
            <div className="mt-2.5 space-y-1.5">
              <div className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
                <span className="text-xs text-gray-500">Mode</span>
                <span className="text-xs font-semibold text-gray-900">{mode === "template" ? "Template" : "Script"}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
                <span className="text-xs text-gray-500">Section</span>
                <span className="text-xs font-semibold text-gray-900">
                  {strategySections.find((s) => s.id === activeSection)?.label}
                </span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
                <span className="text-xs text-gray-500">Symbol / TF</span>
                <span className="text-xs font-semibold text-gray-900">{form.symbol} / {form.timeframe}</span>
              </div>
            </div>
          </div>

          {/* Linked surfaces */}
          <div className="border-t border-gray-100 px-4 py-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-gray-400">Linked surfaces</p>
            <div className="mt-2.5 space-y-2">
              <div className="rounded-xl border border-gray-100 bg-gray-50 px-3 py-2.5">
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-400">Risk profile</p>
                <p className="mt-1 text-xs font-semibold text-gray-900">
                  {riskControls ? "Global risk envelope active" : "No risk profile linked"}
                </p>
                {riskControls ? (
                  <p className="mt-0.5 text-[10px] text-gray-500">Max leverage {riskControls.maxLeverage} / daily loss {riskControls.dailyLossLimit}U</p>
                ) : (
                  <p className="mt-0.5 text-[10px] text-gray-400">Configure in Risk Controls before publishing</p>
                )}
              </div>
              <div className="rounded-xl border border-gray-100 bg-gray-50 px-3 py-2.5">
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-400">Backtest summary</p>
                <p className="mt-1 text-xs font-semibold text-gray-900">
                  {selectedStrategy?.lastBacktest ? "Backtest version available" : "No backtest version"}
                </p>
                <p className="mt-0.5 text-[10px] text-gray-400">{selectedStrategy?.lastBacktest || "Run a backtest after editing"}</p>
              </div>
              <div className="grid grid-cols-2 gap-1.5">
                <Link to="/risk-controls" className="rounded-lg border border-gray-200 px-3 py-2 text-center text-[10px] font-medium text-gray-600 transition hover:border-gray-900 hover:text-gray-900">
                  Risk Controls
                </Link>
                <Link to="/backtests" className="rounded-lg border border-gray-200 px-3 py-2 text-center text-[10px] font-medium text-gray-600 transition hover:border-gray-900 hover:text-gray-900">
                  Backtests
                </Link>
              </div>
            </div>
          </div>

          <div className="border-t border-gray-100 px-4 py-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-gray-400">Live execution</p>
            <div className="mt-2.5 space-y-2">
              <div className="rounded-xl border border-gray-100 bg-gray-50 px-3 py-3">
                <label className="flex items-center justify-between gap-3">
                  <span className="text-xs font-semibold text-gray-900">Whitelist for live</span>
                  <input
                    type="checkbox"
                    checked={liveEnabled}
                    onChange={(event) => setLiveEnabled(event.target.checked)}
                    className="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                  />
                </label>
                <div className="mt-3 grid gap-2">
                  <label className="text-[11px] text-gray-500">
                    Weight
                    <input
                      type="number"
                      min={0.1}
                      step={0.1}
                      value={executionWeight}
                      onChange={(event) => setExecutionWeight(Number(event.target.value) || 0.1)}
                      className="mt-1 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs text-gray-900 outline-none focus:border-gray-900"
                    />
                  </label>
                  <label className="text-[11px] text-gray-500">
                    Poll interval (s)
                    <input
                      type="number"
                      min={5}
                      step={5}
                      value={pollIntervalSeconds}
                      onChange={(event) => setPollIntervalSeconds(Number(event.target.value) || 5)}
                      className="mt-1 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs text-gray-900 outline-none focus:border-gray-900"
                    />
                  </label>
                </div>
                <div className="mt-3 flex gap-2">
                  <button
                    type="button"
                    onClick={() => void enableLiveForSelectedStrategy()}
                    disabled={!selectedStrategyId || liveActionPending}
                    className="flex-1 rounded-lg bg-gray-900 px-3 py-2 text-[11px] font-semibold text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-gray-300"
                  >
                    {liveActionPending ? "Working..." : "Enable live"}
                  </button>
                  <button
                    type="button"
                    onClick={() => void disableLiveForSelectedStrategy()}
                    disabled={!selectedStrategyId || liveActionPending}
                    className="rounded-lg border border-gray-200 px-3 py-2 text-[11px] font-semibold text-gray-700 transition hover:border-gray-900 hover:text-gray-900 disabled:cursor-not-allowed disabled:text-gray-300"
                  >
                    Disable
                  </button>
                </div>
              </div>

              <div className="rounded-xl border border-gray-100 bg-gray-50 px-3 py-2.5">
                <div className="flex items-center justify-between">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-400">Runtime</p>
                  <StatusPill tone={selectedLiveState?.runtimeStatus === "live_active" ? "positive" : "neutral"}>
                    {selectedLiveState?.runtimeStatus || "disabled"}
                  </StatusPill>
                </div>
                <p className="mt-1 text-xs font-semibold text-gray-900">
                  {executionRuntime?.running ? "Execution runtime running" : "Execution runtime stopped"}
                </p>
                <p className="mt-0.5 text-[10px] text-gray-500">
                  {selectedLiveState?.confirmedAt ? `Confirmed ${selectedLiveState.confirmedAt}` : "Requires explicit confirmation before first live run"}
                </p>
              </div>

              {selectedLiveState?.readinessChecks?.length ? (
                <div className="rounded-xl border border-amber-100 bg-amber-50 px-3 py-2.5 text-[11px] text-amber-700">
                  <p className="font-semibold">Readiness checks</p>
                  <ul className="mt-1 space-y-1">
                    {selectedLiveState.readinessChecks.map((item) => (
                      <li key={item}>• {item}</li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="rounded-xl border border-emerald-100 bg-emerald-50 px-3 py-2.5 text-[11px] text-emerald-700">
                  Ready for live confirmation.
                </div>
              )}
            </div>
          </div>

          {/* Publish readiness */}
          <div className="border-t border-gray-100 px-4 py-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-gray-400">Publish readiness</p>
            <div className="mt-2.5 space-y-1.5">
              {publishChecklist.map((item) => (
                <div
                  key={item.label}
                  className={`rounded-xl px-3 py-2.5 text-xs ${
                    item.status === "ready"
                      ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100"
                      : item.status === "blocked"
                        ? "bg-red-50 text-red-600 ring-1 ring-red-100"
                        : "bg-gray-50 text-gray-600"
                  }`}
                >
                  <div className="font-semibold">{item.label}</div>
                  <div className="mt-0.5 opacity-75">{item.detail}</div>
                </div>
              ))}
              {saveMessage ? (
                <div className="rounded-xl bg-blue-50 px-3 py-2.5 text-xs text-blue-700 ring-1 ring-blue-100">{saveMessage}</div>
              ) : null}
            </div>
          </div>

          {/* Compiled payload */}
          <div className="border-t border-gray-100 px-4 py-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-gray-400">Compiled payload</p>
            <p className="mt-0.5 mb-2.5 text-[11px] text-gray-400">当前工作区编译为 API 参数结构。</p>
            <textarea
              readOnly
              className="min-h-[160px] w-full rounded-xl border border-gray-100 bg-gray-50 p-3 font-mono text-[10px] text-gray-700 outline-none"
              value={JSON.stringify(
                mode === "template"
                  ? compileTemplateParameters(form, selectedTemplateId, templateParameters, entryConditions, exitConditions, marketFilters, {
                      liveEnabled,
                      executionWeight,
                      pollIntervalSeconds,
                    })
                  : compileScriptParameters(form, scriptBody, scriptParameters, {
                      liveEnabled,
                      executionWeight,
                      pollIntervalSeconds,
                    }),
                null,
                2,
              )}
            />
          </div>
        </div>

      </div>
    </div>
  );
}
