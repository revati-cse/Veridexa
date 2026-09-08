"use client";

import { useState } from "react";
import { Users, Gauge, ShieldCheck, ShieldAlert, Search } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { RecruiterDashboardResponse } from "@/lib/types";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";
import { EmptyState } from "@/components/shared/EmptyState";
import { Card } from "@/components/shared/Card";
import { Badge, type BadgeTone } from "@/components/shared/Badge";
import { Button } from "@/components/shared/Button";
import { PageHeader } from "@/components/shared/PageHeader";
import { scoreBand, SCORE_BAND_TEXT } from "@/lib/ui";

const STATUS_LABEL: Record<ReturnType<typeof scoreBand>, string> = {
  strong: "Ready",
  moderate: "Developing",
  weak: "Emerging",
};

const STATUS_TONE: Record<ReturnType<typeof scoreBand>, BadgeTone> = {
  strong: "success",
  moderate: "warning",
  weak: "danger",
};

function StatTile({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <Card padding="sm" className="flex items-center gap-3">
      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-indigo-50 text-indigo-600">
        <Icon size={16} />
      </span>
      <div>
        <p className="text-lg font-bold leading-none text-slate-900">{value}</p>
        <p className="mt-1 text-xs text-slate-500">{label}</p>
      </div>
    </Card>
  );
}

function topSkills(candidate: RecruiterDashboardResponse["candidates"][number], n = 2) {
  return [...candidate.skill_breakdown]
    .sort((a, b) => b.score - a.score)
    .slice(0, n)
    .map((s) => s.skill);
}

export default function RecruiterPage() {
  const [jobId, setJobId] = useState("");
  const [dashboard, setDashboard] = useState<RecruiterDashboardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  async function fetchDashboard() {
    if (!jobId.trim()) return;
    setLoading(true);
    setError(null);
    setDashboard(null);
    setSelected(new Set());
    try {
      setDashboard(await api.getRecruiterDashboard(jobId.trim()));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load the recruiter dashboard.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    fetchDashboard();
  }

  function toggleSelected(userId: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(userId)) next.delete(userId);
      else next.add(userId);
      return next;
    });
  }

  const candidates = dashboard?.candidates ?? [];
  const selectedCandidates = candidates.filter((c) => selected.has(c.user_id));
  const avgReadiness =
    candidates.length > 0 ? Math.round(candidates.reduce((sum, c) => sum + c.readiness_score, 0) / candidates.length) : 0;
  const verifiedSkillCount = new Set(
    candidates.flatMap((c) => c.skill_breakdown.filter((s) => scoreBand(s.score) === "strong").map((s) => s.skill))
  ).size;
  const gapSkillCount = new Set(candidates.flatMap((c) => c.skill_gaps.map((g) => g.skill))).size;

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <PageHeader
        eyebrow="Recruiter View"
        title="Rank candidates by proven capability"
        subtitle="Every readiness score below is computed by the exact same formula the candidate sees on their own dashboard — from persisted challenge history, not a separate recruiter-side number."
      />

      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Search size={15} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={jobId}
            onChange={(e) => setJobId(e.target.value)}
            placeholder="Paste a Job ID (shown on the Skills screen after analyzing a job description)"
            className="w-full rounded-lg border border-slate-300 py-2.5 pl-9 pr-3 text-sm font-mono focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          />
        </div>
        <Button type="submit" disabled={loading || !jobId.trim()}>
          Load
        </Button>
      </form>

      {loading && <LoadingState label="Loading candidates..." />}
      {error && <ErrorState message={error} onRetry={fetchDashboard} />}

      {dashboard && !dashboard.db_available && (
        <ErrorState message="No database is configured on this backend, so there is no cross-candidate history to show. This is a deployment gap, not a sign that nobody has applied — see docs/demo_script.md." />
      )}

      {dashboard && dashboard.db_available && candidates.length === 0 && (
        <EmptyState message={`No candidates have completed a challenge for "${dashboard.job_title || jobId}" yet.`} />
      )}

      {dashboard && dashboard.db_available && candidates.length > 0 && (
        <>
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{dashboard.job_title}</h2>
            <p className="text-xs text-slate-400">Select two or more candidates below to compare skill-by-skill.</p>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatTile icon={Users} label="Candidates" value={String(candidates.length)} />
            <StatTile icon={Gauge} label="Avg. Readiness" value={`${avgReadiness}%`} />
            <StatTile icon={ShieldCheck} label="Verified Skills" value={String(verifiedSkillCount)} />
            <StatTile icon={ShieldAlert} label="Skill Gaps" value={String(gapSkillCount)} />
          </div>

          <Card padding="none" className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] border-collapse text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-400">
                    <th className="w-10 py-3 pl-4" />
                    <th className="py-3">Candidate</th>
                    <th className="py-3">Readiness</th>
                    <th className="py-3">Challenges</th>
                    <th className="py-3">Top Skills</th>
                    <th className="py-3">Status</th>
                    <th className="py-3 pr-4">Top Skill Gaps</th>
                  </tr>
                </thead>
                <tbody>
                  {candidates.map((candidate) => {
                    const band = scoreBand(candidate.readiness_score);
                    return (
                      <tr key={candidate.user_id} className="border-b border-slate-100 align-top last:border-0">
                        <td className="py-3 pl-4">
                          <input
                            type="checkbox"
                            checked={selected.has(candidate.user_id)}
                            onChange={() => toggleSelected(candidate.user_id)}
                            aria-label={`Select candidate ${candidate.user_id.slice(0, 8)} for comparison`}
                          />
                        </td>
                        <td className="py-3 font-mono text-xs text-slate-600">{candidate.user_id.slice(0, 8)}</td>
                        <td className={`py-3 font-semibold ${SCORE_BAND_TEXT[band]}`}>{candidate.readiness_score}%</td>
                        <td className="py-3 text-slate-600">{candidate.challenges_completed}</td>
                        <td className="py-3">
                          <div className="flex flex-wrap gap-1">
                            {topSkills(candidate).map((s) => (
                              <Badge key={s} tone="neutral">
                                {s}
                              </Badge>
                            ))}
                          </div>
                        </td>
                        <td className="py-3">
                          <Badge tone={STATUS_TONE[band]}>{STATUS_LABEL[band]}</Badge>
                        </td>
                        <td className="py-3 pr-4 text-slate-500">
                          {candidate.skill_gaps.length > 0 ? candidate.skill_gaps.map((g) => g.skill).join(", ") : "None"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}

      {selectedCandidates.length >= 2 && (
        <Card className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-slate-700">Comparing {selectedCandidates.length} candidates</h2>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[480px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-400">
                  <th className="py-2 font-medium">Skill</th>
                  {selectedCandidates.map((c) => (
                    <th key={c.user_id} className="py-2 font-mono text-xs font-medium">
                      {c.user_id.slice(0, 8)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {selectedCandidates[0].skill_breakdown.map((row) => (
                  <tr key={row.skill} className="border-b border-slate-100">
                    <td className="py-2.5 font-medium text-slate-900">
                      {row.skill} <span className="text-xs text-slate-400">({row.importance})</span>
                    </td>
                    {selectedCandidates.map((c) => {
                      const score = c.skill_breakdown.find((r) => r.skill === row.skill)?.score;
                      return (
                        <td key={c.user_id} className={score !== undefined ? SCORE_BAND_TEXT[scoreBand(score)] : "py-2.5 text-slate-400"}>
                          {score !== undefined ? `${score}%` : "—"}
                        </td>
                      );
                    })}
                  </tr>
                ))}
                <tr>
                  <td className="py-2.5 font-semibold text-slate-900">Overall Readiness</td>
                  {selectedCandidates.map((c) => (
                    <td key={c.user_id} className={`py-2.5 font-semibold ${SCORE_BAND_TEXT[scoreBand(c.readiness_score)]}`}>
                      {c.readiness_score}%
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
