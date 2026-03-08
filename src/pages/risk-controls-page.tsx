import { Card } from "../components/ui/card";
import { SectionTitle } from "../components/ui/section-title";

const controls = [
  "Max position notional per strategy",
  "Daily loss threshold and auto-stop",
  "Market whitelist per execution account",
  "Trading session windows",
  "Manual kill switch with audit trail",
];

export function RiskControlsPage() {
  return (
    <Card>
      <SectionTitle
        eyebrow="Risk posture"
        title="Control frame"
        description="Risk stays explicit and versioned so strategy logic never hides execution guardrails."
      />
      <div className="grid gap-4 md:grid-cols-2">
        {controls.map((control) => (
          <div key={control} className="rounded-[24px] border border-rose-400/10 bg-rose-400/5 p-5 text-sm text-slate-200">
            {control}
          </div>
        ))}
      </div>
    </Card>
  );
}
