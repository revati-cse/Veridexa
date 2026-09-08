"use client";

import Link from "next/link";
import { useSessionStore } from "@/lib/store";
import { EmptyState } from "@/components/shared/EmptyState";

const CRITERION_LABEL: Record<string, string> = {
  correctness: "Correctness",
  technical_logic: "Technical Logic",
  reasoning: "Reasoning",
  edge_cases: "Edge Cases",
  efficiency: "Efficiency",
};

export default function EvaluationPage() {
  const evaluation = useSessionStore((s) => s.evaluation);

  if (!evaluation) {
    return (
      <EmptyState
        message="No evaluation yet."
        action={
          <Link href="/challenge" className="text-slate-900 underline">
            Go complete a challenge
          </Link>
        }
      />
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-semibold">AI Evaluation</h2>
        <p className="mt-1 text-4xl font-bold">{evaluation.overall_score}%</p>
        <p className="text-slate-500">Overall performance</p>
      </div>

      <div className="flex flex-col gap-2">
        <h3 className="font-semibold">Rubric Scores</h3>
        {Object.entries(evaluation.rubric_scores).map(([criterion, score]) => (
          <div key={criterion} className="flex items-center gap-3">
            <span className="w-36 text-sm text-slate-600">{CRITERION_LABEL[criterion] ?? criterion}</span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
              <div className="h-2 rounded-full bg-slate-900" style={{ width: `${score}%` }} />
            </div>
            <span className="w-10 text-right text-sm text-slate-600">{score}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <h3 className="font-semibold text-green-700">Strengths</h3>
          {evaluation.strengths.length > 0 ? (
            <ul className="mt-1 list-inside list-disc text-sm text-slate-700">
              {evaluation.strengths.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-sm text-slate-400">None identified yet.</p>
          )}
        </div>
        <div>
          <h3 className="font-semibold text-amber-700">Weaknesses</h3>
          {evaluation.weaknesses.length > 0 ? (
            <ul className="mt-1 list-inside list-disc text-sm text-slate-700">
              {evaluation.weaknesses.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-sm text-slate-400">None identified yet.</p>
          )}
        </div>
      </div>

      {evaluation.evidence.length > 0 && (
        <div>
          <h3 className="font-semibold">Evidence</h3>
          <ul className="mt-1 flex flex-col gap-1 text-sm text-slate-700">
            {evaluation.evidence.map((e) => (
              <li key={e.skill + e.observation}>
                <span className="font-medium">{e.skill}:</span> {e.observation}
              </li>
            ))}
          </ul>
        </div>
      )}

      <Link
        href="/readiness"
        className="self-start rounded-md bg-slate-900 px-5 py-2.5 font-medium text-white hover:bg-slate-700"
      >
        View Job Readiness
      </Link>
    </div>
  );
}
