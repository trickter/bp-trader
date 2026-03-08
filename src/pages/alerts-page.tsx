import { Card } from "../components/ui/card";
import { SectionTitle } from "../components/ui/section-title";
import { StatusPill } from "../components/ui/status-pill";
import { useDashboardData } from "../hooks/use-dashboard-data";
import { api } from "../lib/api";

export function AlertsPage() {
  const alerts = useDashboardData(api.alerts, []);

  return (
    <Card>
      <SectionTitle
        eyebrow="Alert stream"
        title="Operational alerts"
        description="Backtests, data freshness, risk transitions, and credential events are routed into a single admin feed."
      />
      <div className="space-y-4">
        {alerts.data.map((alert) => (
          <div
            key={alert.id}
            className="rounded-[24px] border border-white/8 bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.02))] p-5"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-lg font-semibold text-white">{alert.title}</p>
                <p className="mt-1 text-sm text-slate-400">{alert.detail}</p>
              </div>
              <StatusPill
                tone={
                  alert.level === "critical"
                    ? "negative"
                    : alert.level === "warning"
                      ? "neutral"
                      : "positive"
                }
              >
                {alert.level}
              </StatusPill>
            </div>
            <p className="mt-3 text-xs uppercase tracking-[0.24em] text-slate-500">{alert.occurredAt}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
