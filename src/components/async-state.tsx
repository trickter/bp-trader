import type { ReactNode } from "react";

import { cn } from "../lib/utils";

export function SectionState({
  title,
  detail,
  tone = "neutral",
}: {
  title: string;
  detail: string;
  tone?: "neutral" | "error";
}) {
  return (
    <div
      className={cn(
        "rounded-[24px] border p-6 text-sm",
        tone === "error"
          ? "border-rose-400/20 bg-rose-400/10 text-rose-100"
          : "border-white/8 bg-white/5 text-slate-300",
      )}
    >
      <p className="text-base font-semibold text-white">{title}</p>
      <p className={cn("mt-2", tone === "error" ? "text-rose-100/80" : "text-slate-400")}>{detail}</p>
    </div>
  );
}

export function LoadingBlock({
  rows = 3,
  className,
}: {
  rows?: number;
  className?: string;
}) {
  return (
    <div className={cn("space-y-3", className)}>
      {Array.from({ length: rows }).map((_, index) => (
        <div
          key={index}
          className="h-12 animate-pulse rounded-2xl border border-white/6 bg-white/5"
        />
      ))}
    </div>
  );
}

export function MetricSkeletonGrid({ cards = 4 }: { cards?: number }) {
  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {Array.from({ length: cards }).map((_, index) => (
        <div
          key={index}
          className="h-36 animate-pulse rounded-[28px] border border-white/8 bg-white/5"
        />
      ))}
    </section>
  );
}

export function StateBoundary({
  isLoading,
  hasError,
  isEmpty,
  loadingFallback,
  errorFallback,
  emptyFallback,
  hasData,
  children,
}: {
  isLoading: boolean;
  hasError: boolean;
  isEmpty: boolean;
  loadingFallback: ReactNode;
  errorFallback: ReactNode;
  emptyFallback: ReactNode;
  hasData: boolean;
  children: ReactNode;
}) {
  if (isLoading) {
    return <>{loadingFallback}</>;
  }

  if (hasError) {
    return <>{errorFallback}</>;
  }

  if (isEmpty || !hasData) {
    return <>{emptyFallback}</>;
  }

  return <>{children}</>;
}
