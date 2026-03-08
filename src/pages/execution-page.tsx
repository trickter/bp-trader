import { Card } from "../components/ui/card";
import { SectionTitle } from "../components/ui/section-title";
import { StatusPill } from "../components/ui/status-pill";

const states = [
  "created",
  "submitted",
  "acked",
  "open",
  "partially_filled",
  "filled / canceled / rejected",
];

export function ExecutionPage() {
  return (
    <div className="grid gap-6 xl:grid-cols-[1.35fr_1fr]">
      <Card>
        <SectionTitle
          eyebrow="Execution skeleton"
          title="Order lifecycle"
          description="Live trading is disabled, but the system already tracks the state machine needed for future live rollout."
        />
        <div className="grid gap-3">
          {states.map((state) => (
            <div key={state} className="rounded-2xl border border-white/8 bg-white/5 px-4 py-3 text-sm text-slate-300">
              {state}
            </div>
          ))}
        </div>
      </Card>
      <Card>
        <SectionTitle
          eyebrow="Idempotency"
          title="Command rules"
          description="Order updates are keyed by client_order_id, not inferred from exchange order formats."
        />
        <div className="space-y-4 text-sm text-slate-300">
          <div className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/5 p-4">
            <span>Mode</span>
            <StatusPill>paper-ready</StatusPill>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
            REST submission and WS orderUpdate association share explicit identifiers and timestamps.
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
            Retry rules stay opt-in and are disallowed for non-idempotent transitions.
          </div>
        </div>
      </Card>
    </div>
  );
}
