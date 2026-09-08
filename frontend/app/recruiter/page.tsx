"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { RecruiterDashboardResponse } from "@/lib/types";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";
import { EmptyState } from "@/components/shared/EmptyState";

const READINESS_STYLE = (score: number) =>
  score >= 80 ? "text-green-700" : score >= 60 ? "text-amber-700" : "text-red-700";

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

  const selectedCandidates = (dashboard?.candidates ?? []).filter((c) => selected.has(c.user_id));

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-semibold">Recruiter Dashboard</h2>
        <p className="mt-1 text-sm text-slate-500">
          Every candidate&apos;s readiness score below is computed by the exact same formula the candidate sees on
          their own dashboard — from their persisted challenge history, not a separate recruiter-side number.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={jobId}
          onChange={(e) => setJobId(e.target.value)}
          placeholder="Paste a Job ID (shown on the Skills screen after analyzing a job description)"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm font-mono"
        />
        <button
          type="submit"
          disabled={loading || !jobId.trim()}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-40"
        >
          Load
        </button>
      </form>

      {loading && <LoadingState label="Loading candidates..." />}
      {error && <ErrorState message={error} onRetry={fetchDashboard} />}

      {dashboard && !dashboard.db_available && (
        <ErrorState message="No database is configured on this backend, so there is no cross-candidate history to show. This is a deployment gap, not a sign that nobody has applied — see docs/demo_script.md." />
      )}

      {dashboard && dashboard.db_available && dashboard.candidates.length === 0 && (
        <EmptyState message={`No candidates have completed a challenge for "${dashboard.job_title || jobId}" yet.`} />
      )}

      {dashboard && dashboard.db_available && dashboard.candidates.length > 0 && (
        <div>
          <div className="mb-2 flex items-baseline justify-between">
            <h3 className="font-semibold">{dashboard.job_title}</h3>
            <p className="text-xs text-slate-400">Select two or more candidates to compare skill-by-skill.</p>
          </div>
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-slate-500">
                <th className="w-8 py-2" />
                <th className="py-2">Candidate</th>
                <th className="py-2">Readiness</th>
                <th className="py-2">Challenges</th>
                <th className="py-2">Top Skill Gaps</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.candidates.map((candidate) => (
                <tr key={candidate.user_id} className="border-b border-slate-100 align-top">
                  <td className="py-2">
                    <input
                      type="checkbox"
                      checked={selected.has(candidate.user_id)}
                      onChange={() => toggleSelected(candidate.user_id)}
                      aria-label={`Select candidate ${candidate.user_id.slice(0, 8)} for comparison`}
                    />
                  </td>
                  <td className="py-2 font-mono text-xs">{candidate.user_id.slice(0, 8)}</td>
                  <td className={`py-2 font-semibold ${READINESS_STYLE(candidate.readiness_score)}`}>
                    {candidate.readiness_score}%
                  </td>
                  <td className="py-2">{candidate.challenges_completed}</td>
                  <td className="py-2 text-slate-600">
                    {candidate.skill_gaps.length > 0
                      ? candidate.skill_gaps.map((g) => g.skill).join(", ")
                      : "None"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selectedCandidates.length >= 2 && (
        <div>
          <h3 className="mb-2 font-semibold">Comparing {selectedCandidates.length} candidates</h3>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-slate-500">
                  <th className="py-2">Skill</th>
                  {selectedCandidates.map((c) => (
                    <th key={c.user_id} className="py-2 font-mono text-xs">
                      {c.user_id.slice(0, 8)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {selectedCandidates[0].skill_breakdown.map((row) => (
                  <tr key={row.skill} className="border-b border-slate-100">
                    <td className="py-2 font-medium">
                      {row.skill} <span className="text-xs text-slate-400">({row.importance})</span>
                    </td>
                    {selectedCandidates.map((c) => {
                      const score = c.skill_breakdown.find((r) => r.skill === row.skill)?.score;
                      return (
                        <td key={c.user_id} className={`py-2 ${score !== undefined ? READINESS_STYLE(score) : "text-slate-400"}`}>
                          {score !== undefined ? `${score}%` : "—"}
                        </td>
                      );
                    })}
                  </tr>
                ))}
                <tr>
                  <td className="py-2 font-semibold">Overall Readiness</td>
                  {selectedCandidates.map((c) => (
                    <td key={c.user_id} className={`py-2 font-semibold ${READINESS_STYLE(c.readiness_score)}`}>
                      {c.readiness_score}%
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
