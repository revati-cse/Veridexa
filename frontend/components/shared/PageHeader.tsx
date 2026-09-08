import type { ReactNode } from "react";

/** Consistent eyebrow + title + subtitle block for every screen — keeps
 * heading hierarchy and spacing identical across the whole app. */
export function PageHeader({
  eyebrow,
  title,
  subtitle,
  meta,
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  meta?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      {eyebrow && (
        <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">{eyebrow}</p>
      )}
      <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">{title}</h1>
      {subtitle && <p className="max-w-2xl text-slate-600">{subtitle}</p>}
      {meta}
    </div>
  );
}
