"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Check, Users } from "lucide-react";
import { Logo } from "./Logo";
import { useSessionStore } from "@/lib/store";
import { cn } from "@/lib/ui";

interface Stage {
  n: number;
  label: string;
  href: string;
  done: (s: ReturnType<typeof useSessionStore.getState>) => boolean;
}

const STAGES: Stage[] = [
  { n: 1, label: "Job", href: "/job", done: (s) => s.jobId !== null },
  { n: 2, label: "Skills", href: "/skills", done: (s) => s.job !== null },
  { n: 3, label: "Evidence", href: "/evidence", done: (s) => s.claims.length > 0 || s.githubEvidence !== null },
  { n: 4, label: "Challenge", href: "/challenge", done: (s) => s.evaluation !== null },
  { n: 5, label: "Evaluation", href: "/evaluation", done: (s) => s.evaluation !== null },
  { n: 6, label: "Readiness", href: "/readiness", done: (s) => s.readiness !== null },
];

/** Sticky header with the Veridexa wordmark and a stepper reflecting real
 * session progress (not just "which route am I on") — a stage shows as done
 * once its underlying state actually exists, so the indicator stays honest
 * even if someone jumps around with the browser back button. */
export function Header() {
  const pathname = usePathname();
  const session = useSessionStore();
  const currentStage = STAGES.find((s) => s.href === pathname);

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link href="/" className="shrink-0">
          <Logo size="sm" />
        </Link>

        <nav aria-label="Candidate journey" className="hidden flex-1 items-center justify-center lg:flex">
          <ol className="flex items-center">
            {STAGES.map((stage, i) => {
              const isCurrent = stage.href === pathname;
              const isDone = stage.done(session) && !isCurrent;
              return (
                <li key={stage.href} className="flex items-center">
                  {i > 0 && <span className="mx-1.5 h-px w-6 bg-slate-200" aria-hidden />}
                  <Link
                    href={stage.href}
                    aria-current={isCurrent ? "step" : undefined}
                    className={cn(
                      "flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium transition-colors",
                      isCurrent && "bg-indigo-50 text-indigo-700",
                      isDone && "text-slate-500 hover:text-slate-700",
                      !isCurrent && !isDone && "text-slate-400 hover:text-slate-600"
                    )}
                  >
                    <span
                      className={cn(
                        "grid h-5 w-5 shrink-0 place-items-center rounded-full text-[10px] font-semibold",
                        isCurrent && "bg-indigo-600 text-white",
                        isDone && "bg-emerald-100 text-emerald-700",
                        !isCurrent && !isDone && "bg-slate-100 text-slate-400"
                      )}
                    >
                      {isDone ? <Check size={11} strokeWidth={3} /> : stage.n}
                    </span>
                    {stage.label}
                  </Link>
                </li>
              );
            })}
          </ol>
        </nav>

        <div className="flex items-center gap-3">
          {currentStage && (
            <p className="text-xs font-medium text-slate-500 lg:hidden">
              Step {currentStage.n} of {STAGES.length} · {currentStage.label}
            </p>
          )}
          <Link
            href="/recruiter"
            className={cn(
              "hidden shrink-0 items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors sm:inline-flex",
              pathname === "/recruiter"
                ? "border-indigo-200 bg-indigo-50 text-indigo-700"
                : "border-slate-200 text-slate-600 hover:bg-slate-50"
            )}
          >
            <Users size={14} />
            Recruiter View
          </Link>
        </div>
      </div>
    </header>
  );
}
