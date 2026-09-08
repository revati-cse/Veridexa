"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { useSessionStore } from "@/lib/store";
import { getCandidateId } from "@/lib/candidateId";
import type { ClaimLevel, SkillTaxonomyItem } from "@/lib/types";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";

const CLAIM_LEVELS: ClaimLevel[] = ["beginner", "intermediate", "advanced"];

export default function EvidencePage() {
  const claims = useSessionStore((s) => s.claims);
  const setClaims = useSessionStore((s) => s.setClaims);
  const githubEvidence = useSessionStore((s) => s.githubEvidence);
  const setGithubEvidence = useSessionStore((s) => s.setGithubEvidence);

  const [taxonomy, setTaxonomy] = useState<SkillTaxonomyItem[] | null>(null);
  const [taxonomyError, setTaxonomyError] = useState<string | null>(null);
  const [repoUrl, setRepoUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    loadTaxonomy();
  }, []);

  async function loadTaxonomy() {
    setTaxonomyError(null);
    try {
      setTaxonomy(await api.getTaxonomy());
    } catch (err) {
      setTaxonomyError(err instanceof ApiError ? err.message : "Failed to load skill taxonomy.");
    }
  }

  function toggleClaim(skill: string) {
    const exists = claims.find((c) => c.skill === skill);
    if (exists) {
      setClaims(claims.filter((c) => c.skill !== skill));
    } else {
      setClaims([...claims, { skill, level: "intermediate" }]);
    }
  }

  function setClaimLevel(skill: string, level: ClaimLevel) {
    setClaims(claims.map((c) => (c.skill === skill ? { ...c, level } : c)));
  }

  async function handleSubmit() {
    setSubmitting(true);
    setSubmitError(null);
    const userId = getCandidateId();

    try {
      await api.saveClaims({ user_id: userId, claims });
    } catch (err) {
      setSubmitError(err instanceof ApiError ? `Failed to save claims: ${err.message}` : "Failed to save claims.");
      setSubmitting(false);
      return;
    }

    if (repoUrl.trim()) {
      try {
        const res = await api.analyzeGithub({
          user_id: userId,
          repository_url: repoUrl.trim(),
          claimed_skills: claims,
          required_skills: [],
        });
        setGithubEvidence(res);
      } catch (err) {
        // Claims already saved above — a repo analysis failure shouldn't
        // read as if nothing happened, and it never blocks moving on.
        const detail = err instanceof ApiError ? err.message : "Repository analysis failed.";
        setSubmitError(`${detail} Your claimed skills were saved — you can continue without repository evidence.`);
      }
    }

    setSubmitting(false);
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-semibold">Candidate Evidence</h2>
        <p className="text-slate-600">Claim your skills, then optionally link a GitHub repository for evidence.</p>
      </div>

      {taxonomyError && <ErrorState message={taxonomyError} onRetry={loadTaxonomy} />}
      {!taxonomy && !taxonomyError && <LoadingState label="Loading skill taxonomy..." />}

      {taxonomy && (
        <div className="flex flex-wrap gap-2">
          {taxonomy.map((item) => {
            const claim = claims.find((c) => c.skill === item.name);
            return (
              <div key={item.id} className="flex items-center gap-1">
                <button
                  onClick={() => toggleClaim(item.name)}
                  className={`rounded-full border px-3 py-1 text-sm ${
                    claim ? "border-slate-900 bg-slate-900 text-white" : "border-slate-300 bg-white text-slate-700"
                  }`}
                >
                  {item.name}
                </button>
                {claim && (
                  <select
                    value={claim.level}
                    onChange={(e) => setClaimLevel(item.name, e.target.value as ClaimLevel)}
                    className="rounded-md border border-slate-300 bg-white px-1 py-1 text-xs"
                  >
                    {CLAIM_LEVELS.map((level) => (
                      <option key={level} value={level}>
                        {level}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium text-slate-700">GitHub repository (optional)</label>
        <input
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          placeholder="https://github.com/username/repository"
          className="rounded-md border border-slate-300 px-3 py-2"
        />
      </div>

      {submitError && <ErrorState message={submitError} onRetry={handleSubmit} />}
      {submitting && <LoadingState label="Saving claims and analyzing repository..." />}

      <button
        onClick={handleSubmit}
        disabled={submitting || claims.length === 0}
        className="self-start rounded-md bg-slate-900 px-5 py-2.5 font-medium text-white hover:bg-slate-700 disabled:opacity-40"
      >
        Save Evidence
      </button>

      {githubEvidence && (
        <div className="flex flex-col gap-2">
          <h3 className="font-semibold">Claimed Skills vs. Evidence Found</h3>
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-slate-500">
                <th className="py-2">Skill</th>
                <th className="py-2">Claim</th>
                <th className="py-2">GitHub Evidence</th>
                <th className="py-2">Assessment</th>
              </tr>
            </thead>
            <tbody>
              {githubEvidence.claims_vs_evidence.map((row) => (
                <tr key={row.skill} className="border-b border-slate-100">
                  <td className="py-2 font-medium">{row.skill}</td>
                  <td className="py-2">{row.claim ?? "—"}</td>
                  <td className="py-2 capitalize">{row.repository_evidence}</td>
                  <td className="py-2 text-slate-600">{row.assessment}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Link
        href="/challenge"
        className="self-start rounded-md border border-slate-300 px-5 py-2.5 font-medium hover:bg-slate-100"
      >
        Continue to Real-World Challenge
      </Link>
    </div>
  );
}
