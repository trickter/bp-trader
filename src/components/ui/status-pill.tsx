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
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.2em]",
        tone === "positive" && "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
        tone === "negative" && "bg-red-50 text-red-600 ring-1 ring-red-200",
        tone === "neutral" && "bg-gray-100 text-gray-600",
      )}
    >
      {children}
    </span>
  );
}
