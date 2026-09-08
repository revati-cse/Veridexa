import { FileCode2, Activity, AlertTriangle, Flame } from "lucide-react";
import { Badge } from "@/components/shared/Badge";

const STEPS = [
  { icon: FileCode2, label: "Challenge 1" },
  { icon: Activity, label: "Performance Analysis" },
  { icon: AlertTriangle, label: "Weakness Detected" },
  { icon: Flame, label: "Challenge 2 Mutated" },
];

/** The one deliberate "wow" moment in the demo (BLUEPRINT.md's differentiator):
 * this challenge did not exist five seconds ago — it was written specifically
 * because this candidate struggled with a specific concept. mutationReason is
 * the backend's real explanation, not placeholder copy. */
export function MutationBanner({ mutationReason }: { mutationReason: string | null }) {
  return (
    <div className="flex flex-col gap-4 rounded-xl border border-indigo-200 bg-indigo-50 p-5">
      <div className="flex flex-wrap items-center gap-2">
        <Flame size={16} className="text-indigo-600" />
        <p className="text-sm font-bold uppercase tracking-wide text-indigo-900">
          Your next challenge has been adapted
        </p>
        <Badge tone="brand">Mutated from previous performance</Badge>
      </div>

      {mutationReason && (
        <p className="text-sm leading-relaxed text-indigo-800">
          <span className="font-semibold">Based on your previous performance, </span>
          {mutationReason}
        </p>
      )}

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        {STEPS.map((step, i) => {
          const Icon = step.icon;
          const isLast = i === STEPS.length - 1;
          return (
            <div key={step.label} className="flex items-center gap-2">
              <div className="flex items-center gap-1.5">
                <span
                  className={
                    isLast
                      ? "grid h-7 w-7 shrink-0 place-items-center rounded-full bg-indigo-600 text-white"
                      : "grid h-7 w-7 shrink-0 place-items-center rounded-full bg-white text-indigo-500 ring-1 ring-inset ring-indigo-200"
                  }
                >
                  <Icon size={13} />
                </span>
                <span className={isLast ? "text-xs font-semibold text-indigo-900" : "text-xs text-indigo-600"}>
                  {step.label}
                </span>
              </div>
              {!isLast && <span className="hidden text-indigo-300 sm:inline">→</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}
