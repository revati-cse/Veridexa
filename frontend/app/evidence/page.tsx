"use client";

import { useEffect, useState } from "react";
import { ArrowRight, Github, MessageSquareText, ShieldCheck, ArrowDown, Folder } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useSessionStore } from "@/lib/store";
import { getCandidateId } from "@/lib/candidateId";
import type { ClaimLevel, EvidenceStrength, SkillTaxonomyItem } from "@/lib/types";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";
import { Card } from "@/components/shared/Card";
import { Badge, type BadgeTone } from "@/components/shared/Badge";
import { Button, LinkButton } from "@/components/shared/Button";
import { PageHeader } from "@/components/shared/PageHeader";
import { ProgressBar } from "@/components/shared/ProgressBar";

const CLAIM_LEVELS: ClaimLevel[] = ["beginner", "intermediate", "advanced"];

const STRENGTH_TONE: Record<EvidenceStrength, BadgeTone> = {
  strong: "success",
  moderate: "info",
  weak: "warning",
  none: "neutral",
};

function repoName(url: string): string {
  const parts = url.replace(/\/+$/, "").split("/");
  return parts.slice(-2).join("/") || url;
}

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
        const detail = err instanceof ApiError ? err.message : "Repository analysis failed.";
        setSubmitError(`${detail} Your claimed skills were saved — you can continue without repository evidence.`);
      }
    }

    setSubmitting(false);
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <PageHeader
        eyebrow="Step 3 of 6"
        title="Claims are not enough. Evidence matters."
        subtitle="Tell Veridexa what you believe you know, then let a real GitHub repository back it up. A claim never becomes evidence by itself."
      />

      {/* Mini pipeline */}
      <div className="flex flex-col items-center gap-1.5 text-xs font-medium text-slate-400 sm:flex-row sm:justify-center sm:gap-3">
        <span className="flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-slate-600">
          <MessageSquareText size={12} /> Candidate Claims
        </span>
        <ArrowDown size={12} className="sm:hidden" />
        <span className="hidden sm:inline">→</span>
        <span className="flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-slate-600">
          <Folder size={12} /> Project Evidence
        </span>
        <ArrowDown size={12} className="sm:hidden" />
        <span className="hidden sm:inline">→</span>
        <span className="flex items-center gap-1.5 rounded-full bg-indigo-50 px-3 py-1 text-indigo-700">
          <Github size={12} /> GitHub Evidence
        </span>
      </div>

      <Card className="flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-100 text-slate-600">
            <MessageSquareText size={16} />
          </span>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">What do you claim to know?</h2>
            <p className="text-xs text-slate-500">Select every skill you&apos;d claim on a resume, and how well.</p>
          </div>
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
                    className={
                      claim
                        ? "rounded-full border border-indigo-600 bg-indigo-600 px-3 py-1 text-sm text-white transition-colors"
                        : "rounded-full border border-slate-300 bg-white px-3 py-1 text-sm text-slate-700 transition-colors hover:border-slate-400"
                    }
                  >
                    {item.name}
                  </button>
                  {claim && (
                    <select
                      value={claim.level}
                      onChange={(e) => setClaimLevel(item.name, e.target.value as ClaimLevel)}
                      className="rounded-md border border-slate-300 bg-white px-1.5 py-1 text-xs"
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
      </Card>

      <Card className="flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-indigo-50 text-indigo-600">
            <Github size={16} />
          </span>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Back it up with a GitHub repository</h2>
            <p className="text-xs text-slate-500">Optional, read-only — Veridexa never executes your code.</p>
          </div>
        </div>
        <input
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          placeholder="https://github.com/username/repository"
          className="rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
        />

        {submitError && <ErrorState message={submitError} onRetry={handleSubmit} />}
        {submitting && <LoadingState label="Saving claims and analyzing repository..." />}

        <Button onClick={handleSubmit} disabled={submitting || claims.length === 0} className="self-start">
          Save Evidence
        </Button>
      </Card>

      {githubEvidence && (
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-3 border-indigo-100">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <a
                href={githubEvidence.repository}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 font-mono text-sm font-medium text-indigo-700 hover:underline"
              >
                <Github size={15} />
                {repoName(githubEvidence.repository)}
              </a>
              {githubEvidence.demo_fallback && <Badge tone="neutral">Demo fallback</Badge>}
            </div>
            {githubEvidence.languages_detected.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {githubEvidence.languages_detected.map((l) => (
                  <Badge key={l.language} tone="neutral">
                    {l.language} · {Math.round(l.confidence * 100)}%
                  </Badge>
                ))}
              </div>
            )}
          </Card>

          {githubEvidence.skills.length > 0 && (
            <div className="flex flex-col gap-3">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                <ShieldCheck size={15} className="text-emerald-600" />
                Skills demonstrated in this repository
              </h3>
              {githubEvidence.skills.map((s) => (
                <Card key={s.skill} padding="sm" className="flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-slate-900">{s.skill}</span>
                    <Badge tone={STRENGTH_TONE[s.evidence_strength]}>{s.evidence_strength} evidence</Badge>
                  </div>
                  <ProgressBar label="Confidence" value={Math.round(s.confidence * 100)} />
                  {s.observations.length > 0 && (
                    <ul className="mt-1 list-inside list-disc text-xs text-slate-500">
                      {s.observations.map((o) => (
                        <li key={o}>{o}</li>
                      ))}
                    </ul>
                  )}
                </Card>
              ))}
            </div>
          )}

          {githubEvidence.claims_vs_evidence.length > 0 && (
            <Card className="flex flex-col gap-3">
              <h3 className="text-sm font-semibold text-slate-700">Claim vs. Evidence</h3>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[480px] border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-400">
                      <th className="py-2 font-medium">Skill</th>
                      <th className="py-2 font-medium">
                        <span className="inline-flex items-center gap-1">
                          <MessageSquareText size={11} /> Claim
                        </span>
                      </th>
                      <th className="py-2 font-medium">
                        <span className="inline-flex items-center gap-1">
                          <ShieldCheck size={11} /> Evidence
                        </span>
                      </th>
                      <th className="py-2 font-medium">Assessment</th>
                    </tr>
                  </thead>
                  <tbody>
                    {githubEvidence.claims_vs_evidence.map((row) => (
                      <tr key={row.skill} className="border-b border-slate-100">
                        <td className="py-2.5 font-medium text-slate-900">{row.skill}</td>
                        <td className="py-2.5 capitalize text-slate-600">{row.claim ?? "—"}</td>
                        <td className="py-2.5">
                          <Badge tone={STRENGTH_TONE[row.repository_evidence]}>{row.repository_evidence}</Badge>
                        </td>
                        <td className="py-2.5 text-slate-500">{row.assessment}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      )}

      <LinkButton href="/challenge" variant="secondary" icon={<ArrowRight size={16} />} className="flex-row-reverse self-start">
        Continue to Real-World Challenge
      </LinkButton>
    </div>
  );
}
