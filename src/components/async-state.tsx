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
        "rounded-2xl border p-5 text-sm",
        tone === "error"
          ? "border-red-100 bg-red-50 text-red-700"
          : "border-gray-100 bg-gray-50 text-gray-600",
      )}
    >
      <p className={cn("text-base font-semibold", tone === "error" ? "text-red-700" : "text-gray-900")}>{title}</p>
      <p className={cn("mt-2", tone === "error" ? "text-red-600" : "text-gray-500")}>{detail}</p>
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
          className="h-12 animate-pulse rounded-2xl border border-gray-100 bg-gray-100"
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
          className="h-36 animate-pulse rounded-2xl border border-gray-100 bg-gray-100"
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
