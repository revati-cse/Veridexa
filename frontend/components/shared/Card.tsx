import type { ReactNode } from "react";
import { cn } from "@/lib/ui";

/** The one card shell every screen uses — keeps radius/border/shadow/padding
 * identical everywhere instead of each page hand-rolling its own. */
export function Card({
  children,
  className,
  padding = "md",
}: {
  children: ReactNode;
  className?: string;
  padding?: "sm" | "md" | "lg" | "none";
}) {
  const paddingClass = {
    none: "",
    sm: "p-4",
    md: "p-5 sm:p-6",
    lg: "p-6 sm:p-8",
  }[padding];

  return (
    <div className={cn("rounded-xl border border-slate-200 bg-white shadow-sm", paddingClass, className)}>
      {children}
    </div>
  );
}
