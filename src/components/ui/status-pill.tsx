import { cn } from "../../lib/utils";

export function StatusPill({
  children,
  tone = "neutral",
}: {
  children: string;
  tone?: "positive" | "negative" | "neutral";
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.24em]",
        tone === "positive" && "bg-emerald-400/15 text-emerald-200",
        tone === "negative" && "bg-rose-400/15 text-rose-200",
        tone === "neutral" && "bg-white/8 text-slate-300",
      )}
    >
      {children}
    </span>
  );
}
