import { Card } from "./ui/card";
import { SectionTitle } from "./ui/section-title";

export interface ScriptWorkbenchParameter {
  key: string;
  label: string;
  type: "number" | "text" | "select";
  value: string | number | boolean;
  hint?: string;
  options?: string[];
}

export interface ScriptWorkbenchSignal {
  id: string;
  time: string;
  action: string;
  price: string;
  confidence: string;
}

export interface ScriptWorkbenchLog {
  level: "info" | "warning" | "error";
  message: string;
  time: string;
}

export interface ScriptWorkbenchPublishStep {
  label: string;
  detail: string;
  status: "ready" | "idle" | "blocked";
}

interface Props {
  activeSection: "script_editor" | "script_parameters" | "script_signals" | "script_publish";
  title: string;
  description: string;
  strategyId: string | null;
  scriptName: string;
  scriptBody: string;
  parameters: ScriptWorkbenchParameter[];
  signals: ScriptWorkbenchSignal[];
  logs: ScriptWorkbenchLog[];
  publishChecklist: ScriptWorkbenchPublishStep[];
  accountLabel: string;
  marketLabel: string;
  riskProfileLabel: string;
  validationSummaryLabel: string;
  onScriptBodyChange: (value: string) => void;
  onParameterChange: (key: string, value: string | number) => void;
  onFormat: () => void;
  onExtractParameters: () => void;
  onLoadExample: () => void;
  onValidate: () => void;
  onRunBacktest: () => void;
  onPublish: () => void;
}

export function ScriptStrategyWorkbench({
  activeSection,
  title,
  description,
  strategyId,
  scriptName,
  scriptBody,
  parameters,
  signals,
  logs,
  publishChecklist,
  accountLabel,
  marketLabel,
  riskProfileLabel,
  validationSummaryLabel,
  onScriptBodyChange,
  onParameterChange,
  onFormat,
  onExtractParameters,
  onLoadExample,
  onValidate,
  onRunBacktest,
  onPublish,
}: Props) {
  if (activeSection === "script_editor") {
    return (
      <div className="space-y-5">
        <SectionTitle eyebrow="Script editor" title={title} description={description} />
        <Card>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <div className="text-sm font-semibold text-gray-900">{scriptName}</div>
              <div className="mt-1 text-xs text-gray-500">{strategyId ?? "Unsaved draft"} · {marketLabel}</div>
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={onLoadExample} className="rounded-full border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:border-gray-900 hover:text-gray-900">Load example</button>
              <button type="button" onClick={onFormat} className="rounded-full border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:border-gray-900 hover:text-gray-900">Format</button>
              <button type="button" onClick={onValidate} className="rounded-full bg-gray-900 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-gray-800">Validate</button>
            </div>
          </div>
          <textarea
            className="mt-4 min-h-[420px] w-full rounded-2xl border border-gray-200 bg-gray-950 p-4 font-mono text-sm text-gray-100 outline-none transition focus:border-gray-500"
            value={scriptBody}
            onChange={(event) => onScriptBodyChange(event.target.value)}
            spellCheck={false}
          />
        </Card>
      </div>
    );
  }

  if (activeSection === "script_parameters") {
    return (
      <div className="space-y-5">
        <SectionTitle eyebrow="Extracted parameters" title="Parameter panel" description="从脚本提取的参数可在这里单独修改，不必每次手改代码。" />
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={onExtractParameters} className="rounded-full border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:border-gray-900 hover:text-gray-900">Extract parameters</button>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {parameters.map((parameter) => (
            <Card key={parameter.key}>
              <div className="text-sm font-semibold text-gray-900">{parameter.label}</div>
              <div className="mt-1 text-xs text-gray-500">{parameter.hint ?? parameter.key}</div>
              {parameter.type === "select" ? (
                <select
                  className="mt-3 w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-900"
                  value={String(parameter.value)}
                  onChange={(event) => onParameterChange(parameter.key, event.target.value)}
                >
                  {(parameter.options ?? []).map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              ) : (
                <input
                  className="mt-3 w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-900"
                  value={String(parameter.value)}
                  onChange={(event) => onParameterChange(parameter.key, parameter.type === "number" ? Number(event.target.value) : event.target.value)}
                />
              )}
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (activeSection === "script_signals") {
    return (
      <div className="space-y-5">
        <SectionTitle eyebrow="Signal preview" title="Signals and debug output" description="脚本逻辑的轻量预览，用于快速核对当前策略意图。" />
        <div className="grid gap-4 xl:grid-cols-2">
          <Card>
            <div className="text-sm font-semibold text-gray-900">Recent signals</div>
            <div className="mt-4 space-y-3">
              {signals.map((signal) => (
                <div key={signal.id} className="rounded-xl border border-gray-100 bg-gray-50 p-3">
                  <div className="text-xs font-semibold text-gray-900">{signal.action}</div>
                  <div className="mt-1 text-[11px] text-gray-500">{signal.time} · {signal.price} · confidence {signal.confidence}</div>
                </div>
              ))}
            </div>
          </Card>
          <Card>
            <div className="text-sm font-semibold text-gray-900">Debug logs</div>
            <div className="mt-4 space-y-3">
              {logs.map((log) => (
                <div key={`${log.time}-${log.message}`} className="rounded-xl border border-gray-100 bg-gray-50 p-3">
                  <div className="text-xs font-semibold text-gray-900">{log.level.toUpperCase()}</div>
                  <div className="mt-1 text-[11px] text-gray-500">{log.time} · {log.message}</div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <SectionTitle eyebrow="Publish" title="Validation and handoff" description="脚本模式只展示发布前摘要，不在这里展开回测和风控详情。" />
      <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
        <Card>
          <div className="text-sm font-semibold text-gray-900">Linked surfaces</div>
          <div className="mt-4 space-y-3 text-sm text-gray-600">
            <div className="rounded-xl border border-gray-100 bg-gray-50 p-3">Account: {accountLabel}</div>
            <div className="rounded-xl border border-gray-100 bg-gray-50 p-3">Market scope: {marketLabel}</div>
            <div className="rounded-xl border border-gray-100 bg-gray-50 p-3">Risk profile: {riskProfileLabel}</div>
            <div className="rounded-xl border border-gray-100 bg-gray-50 p-3">Validation: {validationSummaryLabel}</div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button type="button" onClick={onRunBacktest} className="rounded-full border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:border-gray-900 hover:text-gray-900">Open backtests</button>
            <button type="button" onClick={onPublish} className="rounded-full bg-gray-900 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-gray-800">Publish</button>
          </div>
        </Card>
        <Card>
          <div className="text-sm font-semibold text-gray-900">Publish checklist</div>
          <div className="mt-4 space-y-3">
            {publishChecklist.map((step) => (
              <div
                key={step.label}
                className={`rounded-xl px-3 py-3 text-xs ${
                  step.status === "ready"
                    ? "bg-emerald-50 text-emerald-700"
                    : step.status === "blocked"
                      ? "bg-red-50 text-red-700"
                      : "bg-gray-50 text-gray-600"
                }`}
              >
                <div className="font-semibold">{step.label}</div>
                <div className="mt-1 opacity-80">{step.detail}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
