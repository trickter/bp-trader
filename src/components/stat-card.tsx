import { Card } from "./ui/card";
import { StatusPill } from "./ui/status-pill";

export function StatCard({
  label,
  value,
  helper,
  badge,
  tone,
}: {
  label: string;
  value: string;
  helper: string;
  badge?: string;
  tone?: "positive" | "negative" | "neutral";
}) {
  return (
    <Card className="min-h-[142px]">
      <div className="flex h-full flex-col justify-between gap-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="ui-kicker text-[10px] font-semibold text-gray-400">{label}</p>
            <p className="financial-data mt-3 text-3xl font-semibold tracking-[-0.04em] text-gray-900">{value}</p>
          </div>
          {badge ? <StatusPill tone={tone}>{badge}</StatusPill> : null}
        </div>
        <p className="text-sm text-gray-500">{helper}</p>
      </div>
    </Card>
  );
}
