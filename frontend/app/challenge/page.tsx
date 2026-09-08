"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { Beaker, ClipboardList, Database, Target, Send } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useSessionStore } from "@/lib/store";
import { getCandidateId } from "@/lib/candidateId";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";
import { EmptyState } from "@/components/shared/EmptyState";
import { Card } from "@/components/shared/Card";
import { Badge } from "@/components/shared/Badge";
import { Button } from "@/components/shared/Button";
import { PageHeader } from "@/components/shared/PageHeader";
import { DatasetTables } from "@/components/challenge/DatasetTables";
import { MutationBanner } from "@/components/challenge/MutationBanner";

// monaco-editor touches `window` at module scope, which breaks Next.js's
// static prerendering even inside a "use client" component — ssr: false
// keeps it out of the server render entirely, only loading in the browser.
const MonacoSqlEditor = dynamic(
  () => import("@/components/challenge/MonacoSqlEditor").then((mod) => mod.MonacoSqlEditor),
  { ssr: false, loading: () => <LoadingState label="Loading code editor..." /> }
);

const DIFFICULTY_LABEL: Record<number, string> = { 1: "Junior", 2: "Mid-level", 3: "Senior" };

function DifficultyDots({ level }: { level: number }) {
  return (
    <span className="inline-flex items-center gap-1" aria-label={`Difficulty ${level} of 3`}>
      {[1, 2, 3].map((n) => (
        <span key={n} className={`h-1.5 w-1.5 rounded-full ${n <= level ? "bg-indigo-500" : "bg-slate-200"}`} />
      ))}
    </span>
  );
}

export default function ChallengePage() {
  const router = useRouter();
  const jobId = useSessionStore((s) => s.jobId);
  const job = useSessionStore((s) => s.job);
  const challenge = useSessionStore((s) => s.currentChallenge);
  const setCurrentChallenge = useSessionStore((s) => s.setCurrentChallenge);
  const setEvaluation = useSessionStore((s) => s.setEvaluation);
  const addSubmissionRecord = useSessionStore((s) => s.addSubmissionRecord);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [explanation, setExplanation] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    if (!challenge && jobId && job) {
      generateChallenge();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId, job]);

  async function generateChallenge() {
    if (!jobId || !job) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.generateChallenge({
        job_id: jobId,
        job_title: job.title,
        user_id: getCandidateId(),
        required_skills: job.required_skills.map((rs) => rs.skill),
        difficulty: 1,
      });
      setCurrentChallenge(res.challenge);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to generate a challenge.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit() {
    if (!challenge) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const res = await api.submitSolution({
        challenge,
        user_id: getCandidateId(),
        code,
        explanation,
      });
      setEvaluation(res);
      addSubmissionRecord(challenge, res);
      router.push("/evaluation");
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : "Failed to submit your solution.");
    } finally {
      setSubmitting(false);
    }
  }

  if (!jobId || !job) {
    return (
      <EmptyState
        message="No job in progress."
        action={
          <Link href="/job" className="text-sm font-medium text-indigo-600 hover:text-indigo-700">
            Start by analyzing a job description
          </Link>
        }
      />
    );
  }

  if (loading) return <LoadingState label="Generating your challenge..." />;
  if (error) return <ErrorState message={error} onRetry={generateChallenge} />;
  if (!challenge) return <EmptyState message="No challenge yet." />;

  const isMutated = Boolean(challenge.parent_challenge_id);
  const criteria = Object.entries(challenge.evaluation_criteria);

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      {isMutated && <MutationBanner mutationReason={challenge.mutation_reason} />}

      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <Badge tone="brand" icon={<Beaker size={11} />}>
            Real-World Simulation
          </Badge>
          <span className="text-xs text-slate-400">
            {challenge.role} · {DIFFICULTY_LABEL[challenge.difficulty] ?? `Difficulty ${challenge.difficulty}`}
          </span>
          <DifficultyDots level={challenge.difficulty} />
        </div>
        <PageHeader eyebrow="Step 4 of 6" title={challenge.title} />
        {challenge.required_skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {challenge.required_skills.map((s) => (
              <Badge key={s} tone="neutral">
                {s}
              </Badge>
            ))}
          </div>
        )}
      </div>

      <Card className="flex flex-col gap-2">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <ClipboardList size={15} className="text-slate-400" />
          Scenario
        </h2>
        <p className="text-sm leading-relaxed text-slate-700">{challenge.scenario}</p>
        <p className="mt-2 text-sm leading-relaxed text-slate-700">
          <span className="font-semibold text-slate-800">Instructions: </span>
          {challenge.instructions}
        </p>
      </Card>

      {challenge.dataset != null && (
        <Card className="flex flex-col gap-2">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <Database size={15} className="text-slate-400" />
            Dataset
          </h2>
          <DatasetTables dataset={challenge.dataset} />
        </Card>
      )}

      {(criteria.length > 0 || challenge.expected_output) && (
        <Card padding="sm" className="flex flex-col gap-3 border-slate-100 bg-slate-50/60">
          <h2 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <Target size={13} className="text-slate-400" />
            What you&apos;re evaluated on
          </h2>
          {criteria.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {criteria.map(([criterion, weight]) => (
                <Badge key={criterion} tone="neutral">
                  {criterion.replace(/_/g, " ")} · {Math.round(weight * 100)}%
                </Badge>
              ))}
            </div>
          )}
          {challenge.expected_output && (
            <p className="text-xs leading-relaxed text-slate-500">
              <span className="font-medium text-slate-600">Expected output: </span>
              {challenge.expected_output}
            </p>
          )}
        </Card>
      )}

      <Card className="flex flex-col gap-2">
        <label htmlFor="sql-editor" className="text-sm font-semibold text-slate-700">
          SQL / Code
        </label>
        <MonacoSqlEditor value={code} onChange={setCode} />
      </Card>

      <Card className="flex flex-col gap-2">
        <label htmlFor="explanation" className="text-sm font-semibold text-slate-700">
          Explanation
        </label>
        <textarea
          id="explanation"
          value={explanation}
          onChange={(e) => setExplanation(e.target.value)}
          rows={4}
          className="rounded-lg border border-slate-300 p-3 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          placeholder="Explain your approach — why this query, and what you accounted for..."
        />
      </Card>

      {submitError && <ErrorState message={submitError} onRetry={handleSubmit} />}
      {submitting && <LoadingState label="Evaluating your submission..." />}

      <Button
        onClick={handleSubmit}
        disabled={submitting || code.trim().length === 0}
        icon={<Send size={15} />}
        className="flex-row-reverse self-start"
      >
        Submit Solution
      </Button>
    </div>
  );
}
