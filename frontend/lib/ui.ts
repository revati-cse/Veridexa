/** Shared visual tokens so every screen bands scores the same way instead of
 * each page re-deriving its own thresholds (readiness, evaluation, rubric,
 * recruiter comparison all use this). Bands only ever affect color — the
 * underlying number is always the real backend-computed score. */
export type ScoreBand = "strong" | "moderate" | "weak";

export function scoreBand(score: number): ScoreBand {
  if (score >= 75) return "strong";
  if (score >= 50) return "moderate";
  return "weak";
}

export const SCORE_BAND_TEXT: Record<ScoreBand, string> = {
  strong: "text-emerald-700",
  moderate: "text-amber-700",
  weak: "text-rose-700",
};

export const SCORE_BAND_BAR: Record<ScoreBand, string> = {
  strong: "bg-emerald-500",
  moderate: "bg-amber-500",
  weak: "bg-rose-500",
};

export const SCORE_BAND_BG: Record<ScoreBand, string> = {
  strong: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  moderate: "bg-amber-50 text-amber-700 ring-amber-600/20",
  weak: "bg-rose-50 text-rose-700 ring-rose-600/20",
};

import { twMerge } from "tailwind-merge";

/** Tailwind resolves two conflicting same-specificity utilities (e.g.
 * `bg-white` vs `bg-indigo-600`) by their order in the *generated*
 * stylesheet, not by their order in the class attribute — so a naive
 * `join(" ")` here would let a component's hardcoded base class silently
 * beat a caller's override depending on Tailwind's internal color
 * ordering, regardless of which one is "supposed" to win. twMerge
 * resolves same-group conflicts correctly (last one wins, as intended). */
export function cn(...classes: Array<string | false | null | undefined>): string {
  return twMerge(classes.filter(Boolean).join(" "));
}
