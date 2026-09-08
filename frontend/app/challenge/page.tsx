"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useSessionStore } from "@/lib/store";
import { getCandidateId } from "@/lib/candidateId";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";
import { EmptyState } from "@/components/shared/EmptyState";

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
          <Link href="/job" className="text-slate-900 underline">
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

  return (
    <div className="flex flex-col gap-5">
      {isMutated && (
        <div className="rounded-md border border-indigo-200 bg-indigo-50 px-4 py-3 text-indigo-900">
          <p className="font-medium">Challenge mutated based on your previous performance.</p>
          {challenge.mutation_reason && <p className="mt-1 text-sm text-indigo-700">{challenge.mutation_reason}</p>}
        </div>
      )}

      <div>
        <h2 className="text-2xl font-semibold">{challenge.title}</h2>
        <p className="text-sm text-slate-500">
          {challenge.role} · Difficulty {challenge.difficulty}
        </p>
      </div>

      <p className="text-slate-700">{challenge.scenario}</p>
      <p className="text-slate-700">
        <span className="font-medium">Instructions: </span>
        {challenge.instructions}
      </p>

      {challenge.dataset != null && (
        <pre className="overflow-x-auto rounded-md bg-slate-900 p-3 text-xs text-slate-100">
          {JSON.stringify(challenge.dataset, null, 2)}
        </pre>
      )}

      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium text-slate-700">SQL / Code</label>
        {/* Monaco editor swaps in for this textarea in Phase 7 — plain textarea proves the wiring for now. */}
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          rows={8}
          className="rounded-md border border-slate-300 p-3 font-mono text-sm"
          placeholder="SELECT ..."
        />
      </div>

      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium text-slate-700">Explanation</label>
        <textarea
          value={explanation}
          onChange={(e) => setExplanation(e.target.value)}
          rows={4}
          className="rounded-md border border-slate-300 p-3 text-sm"
          placeholder="Explain your approach..."
        />
      </div>

      {submitError && <ErrorState message={submitError} onRetry={handleSubmit} />}
      {submitting && <LoadingState label="Evaluating your submission..." />}

      <button
        onClick={handleSubmit}
        disabled={submitting || code.trim().length === 0}
        className="self-start rounded-md bg-slate-900 px-5 py-2.5 font-medium text-white hover:bg-slate-700 disabled:opacity-40"
      >
        Submit Solution
      </button>
    </div>
  );
}
