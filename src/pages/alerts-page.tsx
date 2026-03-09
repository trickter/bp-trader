import { LoadingBlock, SectionState } from "../components/async-state";
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
      {alerts.loading ? (
        <LoadingBlock rows={4} />
      ) : alerts.error ? (
        <SectionState
          title="Alert stream failed to load"
          detail={alerts.error}
          tone="error"
        />
      ) : alerts.data.length === 0 ? (
        <SectionState
          title="No alerts right now"
          detail="Critical backtests, data freshness faults, and credential events will surface here."
        />
      ) : (
        <div className="space-y-3">
          {alerts.data.map((alert) => (
            <div
              key={alert.id}
              className="rounded-2xl border border-gray-100 bg-gray-50 p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-gray-900">{alert.title}</p>
                  <p className="mt-1 text-sm text-gray-500">{alert.detail}</p>
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
              <p className="mt-3 text-[10px] font-semibold uppercase tracking-[0.24em] text-gray-400">{alert.occurredAt}</p>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
