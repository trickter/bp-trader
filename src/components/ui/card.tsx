import type { PropsWithChildren } from "react";

import { cn } from "../../lib/utils";

export function Card({
  children,
  className,
}: PropsWithChildren<{ className?: string }>) {
  return (
    <section
      className={cn(
        "rounded-[28px] border border-white/8 bg-[linear-gradient(180deg,rgba(9,20,48,0.9),rgba(5,12,31,0.94))] p-5 shadow-[0_20px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl",
        className,
      )}
    >
      {children}
    </section>
  );
}
