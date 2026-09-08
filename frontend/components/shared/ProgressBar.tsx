import { cn, scoreBand, SCORE_BAND_BAR } from "@/lib/ui";

/** A labeled 0-100 bar, banded by score so a judge can read strong/moderate/
 * weak at a glance without staring at the number — used for rubric criteria
 * and per-skill readiness. `neutral` skips the color banding (e.g. a rubric
 * weight display where "weak" would be a misleading color). */
export function ProgressBar({
  label,
  value,
  maxLabel,
  tone = "banded",
}: {
  label: string;
  value: number;
  maxLabel?: string;
  tone?: "banded" | "neutral";
}) {
  const barClass = tone === "banded" ? SCORE_BAND_BAR[scoreBand(value)] : "bg-indigo-500";
  return (
    <div className="flex items-center gap-3">
      <span className="w-32 shrink-0 text-sm text-slate-600 sm:w-40">{label}</span>
      <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-100">
        <div
          className={cn("h-2.5 rounded-full transition-all duration-500", barClass)}
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </div>
      <span className="w-14 shrink-0 text-right text-sm font-medium text-slate-700">
        {maxLabel ?? `${value}%`}
      </span>
    </div>
  );
}
