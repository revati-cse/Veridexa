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

export default function ReadinessPage() {
  const router = useRouter();
  const jobId = useSessionStore((s) => s.jobId);
  const job = useSessionStore((s) => s.job);
  const claims = useSessionStore((s) => s.claims);
  const githubEvidence = useSessionStore((s) => s.githubEvidence);
  const submissionHistory = useSessionStore((s) => s.submissionHistory);
  const readiness = useSessionStore((s) => s.readiness);
  const setReadiness = useSessionStore((s) => s.setReadiness);
  const currentChallenge = useSessionStore((s) => s.currentChallenge);
  const evaluation = useSessionStore((s) => s.evaluation);
  const setCurrentChallenge = useSessionStore((s) => s.setCurrentChallenge);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mutating, setMutating] = useState(false);
  const [mutateError, setMutateError] = useState<string | null>(null);

  useEffect(() => {
    if (jobId && job) loadReadiness();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId, job, submissionHistory]);

  async function loadReadiness() {
    if (!jobId || !job) return;
    setLoading(true);
    setError(null);
    try {
      setReadiness(
        await api.computeReadiness({
          user_id: getCandidateId(),
          job_id: jobId,
          job_title: job.title,
          required_skills: job.required_skills,
          claims,
          github_evidence: githubEvidence,
          submission_history: submissionHistory,
        })
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load readiness.");
    } finally {
      setLoading(false);
    }
  }

  async function handleImprove() {
    if (!currentChallenge || !evaluation || !jobId || !job) return;
    setMutating(true);
    setMutateError(null);
    try {
      const res = await api.mutateChallenge({
        user_id: getCandidateId(),
        job_id: jobId,
        job_title: job.title,
        required_skills: job.required_skills.map((rs) => rs.skill),
        previous_attempt: { challenge: currentChallenge, evaluation },
      });
      setCurrentChallenge(res.challenge);
      router.push("/challenge");
    } catch (err) {
      setMutateError(err instanceof ApiError ? err.message : "Failed to mutate the next challenge.");
    } finally {
      setMutating(false);
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

  if (loading) return <LoadingState label="Computing job readiness..." />;
  if (error) return <ErrorState message={error} onRetry={loadReadiness} />;
  if (!readiness) return <EmptyState message="No readiness data yet." />;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-semibold">Job Readiness</h2>
        <p className="mt-1 text-5xl font-bold">{readiness.readiness_score}%</p>
        <p className="text-slate-500">{readiness.job_title}</p>
      </div>

      <div>
        <h3 className="font-semibold">Why {readiness.readiness_score}% ready?</h3>
        <p className="mb-2 text-sm text-slate-500">
          Readiness = Σ(skill score × job importance) / Σ(job importance) — computed in the backend, not by the AI.
        </p>
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-slate-500">
              <th className="py-2">Skill</th>
              <th className="py-2">Importance</th>
              <th className="py-2">Score</th>
              <th className="py-2">Weighted Contribution</th>
            </tr>
          </thead>
          <tbody>
            {readiness.skill_breakdown.map((row) => (
              <tr key={row.skill} className="border-b border-slate-100">
                <td className="py-2 font-medium">{row.skill}</td>
                <td className="py-2 capitalize">
                  {row.importance} (×{row.importance_weight})
                </td>
                <td className="py-2">{row.score}</td>
                <td className="py-2">{row.weighted_contribution}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <h3 className="font-semibold text-green-700">Strengths</h3>
          <ul className="mt-1 list-inside list-disc text-sm text-slate-700">
            {readiness.strengths.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="font-semibold text-amber-700">Weaknesses</h3>
          <ul className="mt-1 list-inside list-disc text-sm text-slate-700">
            {readiness.weaknesses.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      </div>

      {readiness.skill_gaps.length > 0 && (
        <div>
          <h3 className="font-semibold">Skill Gaps</h3>
          <ul className="mt-1 flex flex-col gap-1 text-sm text-slate-700">
            {readiness.skill_gaps.map((gap) => (
              <li key={gap.skill}>
                <span className="font-medium">{gap.skill}:</span> {gap.missing_concepts.join(", ")}
              </li>
            ))}
          </ul>
        </div>
      )}

      {mutateError && <ErrorState message={mutateError} onRetry={handleImprove} />}
      {mutating && <LoadingState label="Mutating your next challenge based on your weaknesses..." />}

      <button
        onClick={handleImprove}
        disabled={mutating || !currentChallenge || !evaluation}
        title={!currentChallenge || !evaluation ? "Complete a challenge first" : undefined}
        className="self-start rounded-md bg-slate-900 px-5 py-2.5 font-medium text-white hover:bg-slate-700 disabled:opacity-40"
      >
        Improve My Readiness
      </button>
    </div>
  );
}
