"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ThumbsUp,
  AlertCircle,
  TrendingUp,
  History,
  Target,
  Flame,
  ShieldAlert,
  Info,
  FileSearch,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useSessionStore } from "@/lib/store";
import { getCandidateId } from "@/lib/candidateId";
import type { SkillEvidenceGroup, SkillTimeline } from "@/lib/types";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";
import { EmptyState } from "@/components/shared/EmptyState";
import { Card } from "@/components/shared/Card";
import { Badge } from "@/components/shared/Badge";
import { Button } from "@/components/shared/Button";
import { ScoreRing } from "@/components/shared/ScoreRing";
import { ProgressBar } from "@/components/shared/ProgressBar";

export default function ReadinessPage() {
  const router = useRouter();
  const jobId = useSessionStore((s) => s.jobId);
  const job = useSessionStore((s) => s.job);
  const claims = useSessionStore((s) => s.claims);
  const githubEvidence = useSessionStore((s) => s.githubEvidence);
  const projectDescriptionEvidence = useSessionStore((s) => s.projectDescriptionEvidence);
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
  const [timeline, setTimeline] = useState<SkillTimeline[]>([]);
  const [evidenceTrail, setEvidenceTrail] = useState<SkillEvidenceGroup[]>([]);

  useEffect(() => {
    if (jobId && job) loadReadiness();
    if (submissionHistory.length > 0) loadTimeline();
    if (githubEvidence || projectDescriptionEvidence || submissionHistory.length > 0) loadEvidenceTrail();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId, job, submissionHistory, githubEvidence, projectDescriptionEvidence]);

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
          project_description_evidence: projectDescriptionEvidence,
          submission_history: submissionHistory,
        })
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load readiness.");
    } finally {
      setLoading(false);
    }
  }

  async function loadTimeline() {
    try {
      const res = await api.computeTimeline({ user_id: getCandidateId(), submission_history: submissionHistory });
      setTimeline(res.skills);
    } catch {
      // Skill Evolution is a supplementary view — a failure here shouldn't
      // block the primary readiness screen, so it just stays empty.
    }
  }

  async function loadEvidenceTrail() {
    try {
      const res = await api.computeEvidence({
        user_id: getCandidateId(),
        github_evidence: githubEvidence,
        project_description_evidence: projectDescriptionEvidence,
        submission_history: submissionHistory,
      });
      setEvidenceTrail(res.skills);
    } catch {
      // Supplementary view — a failure here shouldn't block readiness itself.
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
          <Link href="/job" className="text-sm font-medium text-indigo-600 hover:text-indigo-700">
            Start by analyzing a job description
          </Link>
        }
      />
    );
  }

  if (loading) return <LoadingState label="Computing job readiness..." />;
  if (error) return <ErrorState message={error} onRetry={loadReadiness} />;
  if (!readiness) return <EmptyState message="No readiness data yet." />;

  const canImprove = !mutating && Boolean(currentChallenge) && Boolean(evaluation);
  const scoreBySkill = Object.fromEntries(readiness.skill_breakdown.map((r) => [r.skill, r.score]));

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <Card padding="lg" className="flex flex-col items-center gap-4 text-center sm:flex-row sm:items-center sm:gap-8 sm:text-left">
        <ScoreRing value={readiness.readiness_score} label="Estimated Job Readiness" />
        <div className="flex flex-col gap-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">Step 6 of 6 · Job Readiness</p>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">{readiness.job_title}</h1>
          <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
            <Info size={12} />
            Evidence-backed readiness, not a guaranteed hiring score
          </span>
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-700">Skill-wise Readiness</h2>
          <p className="text-xs text-slate-400">Weighted by job importance</p>
        </div>
        <div className="flex flex-col gap-3">
          {readiness.skill_breakdown.map((row) => (
            <div key={row.skill} className="flex flex-col gap-1">
              <ProgressBar label={row.skill} value={row.score} />
              <p className="pl-4 text-[11px] text-slate-400">
                {row.importance} importance (×{row.importance_weight}) · contributes {row.weighted_contribution} to
                the overall score
              </p>
            </div>
          ))}
        </div>
        <p className="mt-1 text-xs text-slate-400">
          Readiness = Σ(skill score × job importance) / Σ(job importance) — computed in the backend, not by the AI.
        </p>
      </Card>

      {evidenceTrail.length > 0 && (
        <Card className="flex flex-col gap-3">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <FileSearch size={15} className="text-indigo-500" />
            Evidence Trail
          </h2>
          <p className="text-xs text-slate-500">
            Every skill score above traces back to one of these — never a bare number with nothing behind it.
          </p>
          <div className="flex flex-col gap-3">
            {evidenceTrail.map((group) => (
              <div key={group.skill}>
                <p className="text-sm font-medium text-slate-800">{group.skill}</p>
                <ul className="mt-1 flex flex-col gap-1">
                  {group.evidence.map((item) => (
                    <li key={item.id} className="flex items-start gap-2 text-xs text-slate-500">
                      <Badge tone="neutral" className="mt-0.5 shrink-0 capitalize">
                        {item.source_type}
                      </Badge>
                      <span>{item.observation}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card className="flex flex-col gap-2">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-emerald-700">
            <ThumbsUp size={15} />
            Strengths
          </h2>
          {readiness.strengths.length > 0 ? (
            <ul className="flex flex-col gap-1.5 text-sm text-slate-700">
              {readiness.strengths.map((s) => (
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
          {readiness.weaknesses.length > 0 ? (
            <ul className="flex flex-col gap-1.5 text-sm text-slate-700">
              {readiness.weaknesses.map((w) => (
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

      {readiness.skill_gaps.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <ShieldAlert size={15} className="text-rose-500" />
            Skill Gaps Detected
          </h2>
          {readiness.skill_gaps.map((gap) => (
            <Card key={gap.skill} className="flex flex-col gap-2 border-rose-100 bg-rose-50/40">
              <div className="flex items-center justify-between">
                <p className="text-sm font-bold text-rose-900">{gap.skill}</p>
                {scoreBySkill[gap.skill] !== undefined && (
                  <span className="text-lg font-bold text-rose-700">{scoreBySkill[gap.skill]}%</span>
                )}
              </div>
              {gap.missing_concepts.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-rose-700">Missing evidence:</p>
                  <ul className="mt-1 flex flex-col gap-1 text-sm text-rose-800">
                    {gap.missing_concepts.map((c) => (
                      <li key={c} className="flex gap-2">
                        <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-rose-400" />
                        {c}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>
          ))}
          <p className="flex items-center gap-1.5 text-xs text-slate-500">
            <Target size={12} className="text-indigo-500" />
            Veridexa recommends a targeted challenge for your top-priority gap.
          </p>
        </div>
      )}

      {submissionHistory.length > 0 && (
        <Card className="flex flex-col gap-2">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <History size={15} className="text-slate-400" />
            Challenge History
          </h2>
          <ul className="flex flex-col divide-y divide-slate-100">
            {submissionHistory.map((record, i) => (
              <li key={record.challenge.id} className="flex items-center justify-between gap-3 py-2.5">
                <div className="flex items-center gap-2">
                  <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-slate-100 text-[11px] font-semibold text-slate-500">
                    {i + 1}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-slate-800">{record.challenge.title}</p>
                    {record.challenge.parent_challenge_id && (
                      <Badge tone="brand" className="mt-0.5">
                        Mutated
                      </Badge>
                    )}
                  </div>
                </div>
                <span className="text-sm font-semibold text-slate-700">{record.evaluation.overall_score}%</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {timeline.some((t) => t.entries.length > 1) && (
        <Card className="flex flex-col gap-2">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <TrendingUp size={15} className="text-indigo-500" />
            Skill Evolution
          </h2>
          <p className="text-xs text-slate-500">
            How each skill&apos;s score has changed across your attempts, including any challenge mutated to target a
            weak point.
          </p>
          <ul className="flex flex-col gap-3">
            {timeline
              .filter((t) => t.entries.length > 1)
              .map((t) => (
                <li key={t.skill}>
                  <p className="text-sm font-medium text-slate-800">
                    {t.skill}:{" "}
                    <span className="font-mono text-sm text-indigo-700">
                      {t.entries.map((e) => `${e.score}%`).join(" → ")}
                    </span>
                  </p>
                  <ul className="mt-1 flex flex-col gap-0.5 text-xs text-slate-500">
                    {t.entries.map((e, i) => (
                      <li key={i}>
                        {e.score}% — {e.challenge_title}
                        {e.mutation_reason && (
                          <span className="italic text-slate-400"> (mutated: {e.mutation_reason})</span>
                        )}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
          </ul>
        </Card>
      )}

      {mutateError && <ErrorState message={mutateError} onRetry={handleImprove} />}
      {mutating && <LoadingState label="Mutating your next challenge based on your weaknesses..." />}

      <Button
        onClick={handleImprove}
        disabled={!canImprove}
        title={!currentChallenge || !evaluation ? "Complete a challenge first" : undefined}
        icon={<Flame size={16} />}
        className="flex-row-reverse self-start"
      >
        Take Next Challenge
      </Button>
    </div>
  );
}
