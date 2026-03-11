import { Card } from "./ui/card";
import { SectionTitle } from "./ui/section-title";
import type { StrategyIndicatorCategory, StrategyTemplatePreset } from "../lib/strategy-builder";

export type ConditionRule = {
  id: string;
  left: string;
  comparator:
    | "crosses_above"
    | "crosses_below"
    | "greater_than"
    | "less_than"
    | "equal_to"
    | "between";
  right: string;
  extra?: string;
  timeframe: string;
  comparisonMode: "indicator_vs_indicator" | "indicator_vs_value" | "price_vs_indicator";
};

export type ConditionGroup = {
  id: string;
  label: string;
  operator: "AND" | "OR";
  rules: ConditionRule[];
  children: ConditionGroup[];
};

export type TemplateParameter = {
  key: string;
  label: string;
  value: string | number | boolean;
  defaultValue: string | number | boolean;
};

interface Props {
  activeSection: "template_library" | "signal_logic" | "parameters" | "indicator_catalog";
  selectedTemplateId: string | null;
  templates: StrategyTemplatePreset[];
  indicatorCategories: StrategyIndicatorCategory[];
  parameters: TemplateParameter[];
  entryConditions: ConditionGroup[];
  exitConditions: ConditionGroup[];
  marketFilters: ConditionGroup[];
  onTemplateSelect: (templateId: string) => void;
  onStartBlank: () => void;
  onParameterChange: (key: string, value: string | number | boolean) => void;
  onResetParameter: (key: string) => void;
  onEntryConditionsChange: (groups: ConditionGroup[]) => void;
  onExitConditionsChange: (groups: ConditionGroup[]) => void;
  onMarketFiltersChange: (groups: ConditionGroup[]) => void;
}

function ConditionBlock({
  title,
  groups,
}: {
  title: string;
  groups: ConditionGroup[];
}) {
  return (
    <div className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
      <p className="text-sm font-semibold text-gray-900">{title}</p>
      <div className="mt-3 space-y-3">
        {groups.map((group) => (
          <div key={group.id} className="rounded-xl border border-white bg-white p-3 shadow-sm">
            <div className="flex items-center justify-between">
              <input
                readOnly
                value={group.label}
                className="w-40 rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs font-semibold text-gray-900"
              />
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-500">
                {group.operator}
              </span>
            </div>
            <div className="mt-3 space-y-2">
              {group.rules.map((rule) => (
                <div key={rule.id} className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2 text-xs text-gray-700">
                  {rule.left} · {rule.comparator} · {rule.right}
                  {rule.extra ? ` · ${rule.extra}` : ""}
                  <span className="ml-2 text-[10px] uppercase tracking-[0.18em] text-gray-400">{rule.timeframe}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function TemplateStrategyBuilder({
  activeSection,
  selectedTemplateId,
  templates,
  indicatorCategories,
  parameters,
  entryConditions,
  exitConditions,
  marketFilters,
  onTemplateSelect,
  onStartBlank,
  onParameterChange,
  onResetParameter,
}: Props) {
  if (activeSection === "template_library") {
    return (
      <Card>
        <SectionTitle
          eyebrow="Template mode"
          title="Create from template"
          description="先选一个预置模板，或者从空白逻辑开始搭建。"
        />
        <div className="grid gap-3 md:grid-cols-2">
          {templates.map((item) => (
            <button
              type="button"
              key={item.id}
              onClick={() => onTemplateSelect(item.id)}
              className={`rounded-2xl border p-4 text-left transition ${
                selectedTemplateId === item.id
                  ? "border-gray-900 bg-gray-900 text-white"
                  : "border-gray-100 bg-gray-50 text-gray-900 hover:border-gray-300"
              }`}
            >
              <p className="text-sm font-semibold">{item.label}</p>
              <p className="mt-2 text-xs opacity-80">{item.summary}</p>
              <div className="mt-3 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] opacity-70">
                <span>{item.market}</span>
                <span>{item.audience}</span>
              </div>
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={onStartBlank}
          className="mt-4 rounded-xl border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 transition hover:border-gray-900 hover:text-gray-900"
        >
          Start from blank
        </button>
      </Card>
    );
  }

  if (activeSection === "parameters") {
    return (
      <Card>
        <SectionTitle
          eyebrow="Parameter panel"
          title="Template parameters"
          description="模板参数集中维护，修改后会直接影响策略逻辑预览。"
        />
        <div className="grid gap-3 md:grid-cols-2">
          {parameters.map((item) => (
            <div key={item.key} className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-gray-500">{item.label}</p>
              <input
                value={String(item.value)}
                onChange={(event) => onParameterChange(item.key, event.target.value)}
                className="mt-2 w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-gray-900"
              />
              <button
                type="button"
                onClick={() => onResetParameter(item.key)}
                className="mt-3 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-semibold text-gray-600 transition hover:border-gray-900 hover:text-gray-900"
              >
                Reset default
              </button>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  if (activeSection === "indicator_catalog") {
    return (
      <Card>
        <SectionTitle
          eyebrow="Indicator catalog"
          title="Indicator selector"
          description="按类别浏览指标，后续可继续补搜索、收藏和最近使用。"
        />
        <div className="grid gap-4 md:grid-cols-2">
          {indicatorCategories.map((category) => (
            <div key={category.id} className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
              <p className="text-sm font-semibold text-gray-900">{category.label}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {category.indicators.map((indicator) => (
                  <span key={indicator} className="rounded-full bg-white px-3 py-1 text-xs text-gray-700 ring-1 ring-gray-200">
                    {indicator}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <SectionTitle
        eyebrow="Signal logic"
        title="Long / entry conditions"
        description="模板模式下使用卡片式条件树定义开仓、平仓和过滤逻辑。"
      />
      <div className="space-y-4">
        <ConditionBlock title="Long / entry conditions" groups={entryConditions} />
        <ConditionBlock title="Exit conditions" groups={exitConditions} />
        <ConditionBlock title="Market filters" groups={marketFilters} />
      </div>
    </Card>
  );
}
