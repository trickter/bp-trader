import { LoadingBlock, SectionState } from "../components/async-state";
import { Card } from "../components/ui/card";
import { SectionTitle } from "../components/ui/section-title";
import { StatusPill } from "../components/ui/status-pill";
import { useDashboardData } from "../hooks/use-dashboard-data";
import { api } from "../lib/api";

export function MarketPulsePage() {
  const metrics = useDashboardData(api.marketPulse, []);

  return (
    <Card>
      <SectionTitle
        eyebrow="Refresh semantics"
        title="Market pulse"
        description="Each tile declares its own freshness contract so operators do not assume uniform real-time guarantees."
      />
      {metrics.loading ? (
        <LoadingBlock rows={6} className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" />
      ) : metrics.error ? (
        <SectionState
          title="Market pulse failed to load"
          detail={metrics.error}
          tone="error"
        />
      ) : metrics.data.length === 0 ? (
        <SectionState
          title="No market pulse metrics"
          detail="The exchange did not return any freshness-aware metrics for this account mode."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {metrics.data.map((metric) => (
            <div
              key={metric.label}
              className="rounded-[24px] border border-white/8 bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.02))] p-5"
            >
              <div className="mb-5 flex items-center justify-between gap-3">
                <p className="text-sm text-slate-300">{metric.label}</p>
                <StatusPill tone={metric.tone}>{metric.freshness}</StatusPill>
              </div>
              <p className="text-3xl font-semibold text-white">{metric.value}</p>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
