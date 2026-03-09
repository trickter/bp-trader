import type { PropsWithChildren } from "react";

import { cn } from "../../lib/utils";

export function Card({
  children,
  className,
}: PropsWithChildren<{ className?: string }>) {
  return (
    <section
      className={cn(
        "rounded-2xl border border-gray-100 bg-white p-6 shadow-sm",
        className,
      )}
    >
      {children}
    </section>
  );
}
