import { cn, scoreBand } from "@/lib/ui";

const RING_COLOR: Record<ReturnType<typeof scoreBand>, string> = {
  strong: "#059669", // emerald-600
  moderate: "#d97706", // amber-600
  weak: "#e11d48", // rose-600
};

/** Pure-CSS conic-gradient ring — no charting dependency for a single
 * number. Deliberately not a full donut chart: this is the one hero score
 * per screen (overall evaluation, overall readiness), not a data series. */
export function ScoreRing({
  value,
  label,
  size = 168,
}: {
  value: number;
  label: string;
  size?: number;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  const color = RING_COLOR[scoreBand(clamped)];
  return (
    <div
      className="relative grid shrink-0 place-items-center rounded-full"
      style={{
        width: size,
        height: size,
        background: `conic-gradient(${color} ${clamped * 3.6}deg, #e2e8f0 0deg)`,
      }}
      role="img"
      aria-label={`${label}: ${clamped}%`}
    >
      <div
        className="grid place-items-center rounded-full bg-white text-center"
        style={{ width: size - 20, height: size - 20 }}
      >
        <div>
          <p className={cn("text-4xl font-bold leading-none text-slate-900")}>{clamped}%</p>
          <p className="mt-1.5 text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
        </div>
      </div>
    </div>
  );
}
