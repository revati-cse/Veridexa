"use client";

import Link from "next/link";
import { ArrowRight, ThumbsUp, AlertCircle, ShieldCheck, Terminal } from "lucide-react";
import { useSessionStore } from "@/lib/store";
import { EmptyState } from "@/components/shared/EmptyState";
import { Card } from "@/components/shared/Card";
import { Badge } from "@/components/shared/Badge";
import { LinkButton } from "@/components/shared/Button";
import { ScoreRing } from "@/components/shared/ScoreRing";
import { ProgressBar } from "@/components/shared/ProgressBar";

const CRITERION_LABEL: Record<string, string> = {
  correctness: "Correctness",
  technical_logic: "Technical Logic",
  reasoning: "Reasoning",
  edge_cases: "Edge Cases",
  efficiency: "Efficiency",
};

export default function EvaluationPage() {
  const evaluation = useSessionStore((s) => s.evaluation);
  const challenge = useSessionStore((s) => s.currentChallenge);
  const weights = challenge?.evaluation_criteria ?? {};

  if (!evaluation) {
    return (
      <EmptyState
        message="No evaluation yet."
        action={
          <Link href="/challenge" className="text-sm font-medium text-indigo-600 hover:text-indigo-700">
            Go complete a challenge
          </Link>
        }
      />
    );
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <Card padding="lg" className="flex flex-col items-center gap-4 text-center sm:flex-row sm:items-center sm:gap-8 sm:text-left">
        <ScoreRing value={evaluation.overall_score} label="Performance Score" />
        <div className="flex flex-col gap-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">AI Evaluation</p>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            The SQL sandbox ran your query for real before any AI reasoning happened.
          </h1>
          {evaluation.demo_fallback && <Badge tone="neutral">Demo fallback</Badge>}
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-slate-700">Rubric Breakdown</h2>
        {Object.entries(evaluation.rubric_scores).map(([criterion, score]) => {
          const weight = weights[criterion];
          const label = CRITERION_LABEL[criterion] ?? criterion;
          return (
            <ProgressBar
              key={criterion}
              label={weight !== undefined ? `${label} (${Math.round(weight * 100)}%)` : label}
              value={score}
            />
          );
        })}
      </Card>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card className="flex flex-col gap-2">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-emerald-700">
            <ThumbsUp size={15} />
            Strengths
          </h2>
          {evaluation.strengths.length > 0 ? (
            <ul className="flex flex-col gap-1.5 text-sm text-slate-700">
              {evaluation.strengths.map((s) => (
                <li key={s} className="flex gap-2">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-emerald-500" />
                  {s}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-400">None identified yet.</p>
          )}
        </Card>
        <Card className="flex flex-col gap-2">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-amber-700">
            <AlertCircle size={15} />
            Weaknesses
          </h2>
          {evaluation.weaknesses.length > 0 ? (
            <ul className="flex flex-col gap-1.5 text-sm text-slate-700">
              {evaluation.weaknesses.map((w) => (
                <li key={w} className="flex gap-2">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-amber-500" />
                  {w}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-400">None identified yet.</p>
          )}
        </Card>
      </div>

      {evaluation.evidence.length > 0 && (
        <Card className="flex flex-col gap-2">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <ShieldCheck size={15} className="text-indigo-500" />
            Evidence &amp; Skill Observations
          </h2>
          <p className="text-xs text-slate-500">This candidate actually demonstrated these skills.</p>
          <ul className="mt-1 flex flex-col gap-1.5 text-sm text-slate-700">
            {evaluation.evidence.map((e) => (
              <li key={e.skill + e.observation} className="flex gap-2">
                <Badge tone="brand" className="mt-0.5 shrink-0">
                  {e.skill}
                </Badge>
                <span className="text-slate-600">{e.observation}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {evaluation.sql_execution_result && (
        <Card padding="sm" className="flex items-center gap-3 border-slate-100 bg-slate-50/60">
          <Terminal size={16} className="shrink-0 text-slate-400" />
          <p className="text-xs text-slate-500">
            {evaluation.sql_execution_result.success
              ? `Query executed successfully — ${evaluation.sql_execution_result.row_count} row(s) returned.`
              : `Query did not execute: ${evaluation.sql_execution_result.error ?? "unknown error"}`}
          </p>
        </Card>
      )}

      <LinkButton href="/readiness" icon={<ArrowRight size={16} />} className="flex-row-reverse self-start">
        View Job Readiness
      </LinkButton>
    </div>
  );
}
