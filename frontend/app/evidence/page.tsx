"use client";

import { useEffect, useState } from "react";
import { ArrowRight, Github, MessageSquareText, ArrowDown, Folder, FileText } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useSessionStore } from "@/lib/store";
import { getCandidateId } from "@/lib/candidateId";
import type { ClaimLevel, SkillTaxonomyItem } from "@/lib/types";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";
import { Card } from "@/components/shared/Card";
import { Button, LinkButton } from "@/components/shared/Button";
import { PageHeader } from "@/components/shared/PageHeader";
import { EvidenceSourcePanel } from "@/components/evidence/EvidenceSourcePanel";

const CLAIM_LEVELS: ClaimLevel[] = ["beginner", "intermediate", "advanced"];
const MIN_DESCRIPTION_LENGTH = 20;

function repoName(url: string): string {
  const parts = url.replace(/\/+$/, "").split("/");
  return parts.slice(-2).join("/") || url;
}

export default function EvidencePage() {
  const claims = useSessionStore((s) => s.claims);
  const setClaims = useSessionStore((s) => s.setClaims);
  const githubEvidence = useSessionStore((s) => s.githubEvidence);
  const setGithubEvidence = useSessionStore((s) => s.setGithubEvidence);
  const projectDescriptionEvidence = useSessionStore((s) => s.projectDescriptionEvidence);
  const setProjectDescriptionEvidence = useSessionStore((s) => s.setProjectDescriptionEvidence);

  const [taxonomy, setTaxonomy] = useState<SkillTaxonomyItem[] | null>(null);
  const [taxonomyError, setTaxonomyError] = useState<string | null>(null);
  const [repoUrl, setRepoUrl] = useState("");
  const [description, setDescription] = useState("");
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

    if (description.trim().length >= MIN_DESCRIPTION_LENGTH) {
      try {
        const res = await api.analyzeProjectDescription({
          user_id: userId,
          description: description.trim(),
          claimed_skills: claims,
          required_skills: [],
        });
        setProjectDescriptionEvidence(res);
      } catch (err) {
        const detail = err instanceof ApiError ? err.message : "Project description analysis failed.";
        setSubmitError(`${detail} Your claimed skills were saved — you can continue without this evidence.`);
      }
    }

    setSubmitting(false);
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <PageHeader
        eyebrow="Step 3 of 6"
        title="Claims are not enough. Evidence matters."
        subtitle="Tell Veridexa what you believe you know, then let a real project back it up. A claim never becomes evidence by itself."
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
      </Card>

      <Card className="flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-100 text-slate-600">
            <FileText size={16} />
          </span>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Or describe a project</h2>
            <p className="text-xs text-slate-500">
              No repository? Describe something you built — what it did, and specifically how you did it.
            </p>
          </div>
        </div>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="e.g. Built a sales dashboard in Power BI on top of a Python ETL script that cleaned raw CSV exports and loaded them into..."
          rows={4}
          className="rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
        />
        <p className="text-xs text-slate-400">
          {description.trim().length > 0 && description.trim().length < MIN_DESCRIPTION_LENGTH
            ? `${MIN_DESCRIPTION_LENGTH - description.trim().length} more characters needed`
            : "Specifics score higher than buzzwords — vague claims stay weak evidence."}
        </p>

        {submitError && <ErrorState message={submitError} onRetry={handleSubmit} />}
        {submitting && <LoadingState label="Saving claims and analyzing evidence..." />}

        <Button onClick={handleSubmit} disabled={submitting || claims.length === 0} className="self-start">
          Save Evidence
        </Button>
      </Card>

      {githubEvidence && (
        <EvidenceSourcePanel
          header={
            <a
              href={githubEvidence.repository}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 font-mono text-sm font-medium text-indigo-700 hover:underline"
            >
              <Github size={15} />
              {repoName(githubEvidence.repository)}
            </a>
          }
          skills={githubEvidence.skills}
          claimsVsEvidence={githubEvidence.claims_vs_evidence}
          demoFallback={githubEvidence.demo_fallback}
        />
      )}

      {projectDescriptionEvidence && (
        <EvidenceSourcePanel
          header={
            <span className="flex items-center gap-2 text-sm font-medium text-slate-700">
              <FileText size={15} className="text-slate-500" />
              Project description
            </span>
          }
          skills={projectDescriptionEvidence.skills}
          claimsVsEvidence={projectDescriptionEvidence.claims_vs_evidence}
          demoFallback={projectDescriptionEvidence.demo_fallback}
        />
      )}

      <LinkButton href="/challenge" variant="secondary" icon={<ArrowRight size={16} />} className="flex-row-reverse self-start">
        Continue to Real-World Challenge
      </LinkButton>
    </div>
  );
}
