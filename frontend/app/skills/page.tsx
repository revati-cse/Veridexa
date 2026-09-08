"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Briefcase, Code2, MessageCircle, Wrench, Copy, Check } from "lucide-react";
import { useSessionStore } from "@/lib/store";
import { api } from "@/lib/api";
import { EmptyState } from "@/components/shared/EmptyState";
import { Card } from "@/components/shared/Card";
import { Badge, type BadgeTone } from "@/components/shared/Badge";
import { LinkButton } from "@/components/shared/Button";
import { PageHeader } from "@/components/shared/PageHeader";
import type { Importance, JobRequiredSkill, SkillCategory } from "@/lib/types";

const IMPORTANCE_TONE: Record<Importance, BadgeTone> = {
  high: "danger",
  medium: "warning",
  low: "neutral",
};

const CATEGORY_LABEL: Record<SkillCategory, string> = {
  programming: "Programming",
  database: "Database",
  data: "Data",
  ai_ml: "AI / ML",
  cloud: "Cloud",
  business: "Business",
  communication: "Communication",
  problem_solving: "Problem Solving",
  tools: "Tools",
};

function SkillChip({ skill, category }: { skill: JobRequiredSkill; category?: SkillCategory }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-4 py-2.5">
      <div className="flex flex-col gap-0.5">
        <span className="text-sm font-medium text-slate-900">{skill.skill}</span>
        {category && <span className="text-[11px] text-slate-400">{CATEGORY_LABEL[category]}</span>}
      </div>
      <Badge tone={IMPORTANCE_TONE[skill.importance]}>{skill.importance}</Badge>
    </div>
  );
}

export default function SkillsPage() {
  const jobId = useSessionStore((s) => s.jobId);
  const job = useSessionStore((s) => s.job);
  const [categoryBySkill, setCategoryBySkill] = useState<Record<string, SkillCategory>>({});
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    // Best-effort enrichment only — job parsing doesn't return a category
    // per skill, so this cross-references the taxonomy for a nicer display.
    // A failure here never blocks the screen; chips just render without it.
    api
      .getTaxonomy()
      .then((items) => {
        const map: Record<string, SkillCategory> = {};
        for (const item of items) map[item.name] = item.category;
        setCategoryBySkill(map);
      })
      .catch(() => {});
  }, []);

  if (!job) {
    return (
      <EmptyState
        message="No job analyzed yet."
        action={
          <Link href="/job" className="text-sm font-medium text-indigo-600 hover:text-indigo-700">
            Go analyze a job description
          </Link>
        }
      />
    );
  }

  const required = job.required_skills.filter((s) => s.required);
  const preferred = job.required_skills.filter((s) => !s.required);

  function copyJobId() {
    if (!jobId) return;
    navigator.clipboard.writeText(jobId).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <PageHeader
        eyebrow="Step 2 of 6"
        title={job.title}
        subtitle="Required skills extracted from the job description, ranked by importance — this is the exact taxonomy row every downstream screen grades against."
      />

      {jobId && (
        <button
          onClick={copyJobId}
          className="inline-flex w-fit items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-500 transition-colors hover:border-indigo-200 hover:text-indigo-700"
        >
          {copied ? <Check size={12} className="text-emerald-600" /> : <Copy size={12} />}
          Job ID: <span className="font-mono">{jobId}</span>
          <span className="text-slate-300">·</span>
          recruiters can look up candidates on the Recruiter View
        </button>
      )}

      <Card className="flex flex-col gap-5">
        <div className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-indigo-50 text-indigo-600">
            <Code2 size={16} />
          </span>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Technical Skills</h2>
        </div>

        {required.length > 0 ? (
          <div className="flex flex-col gap-2">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Required</p>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {required.map((rs) => (
                <SkillChip key={rs.skill} skill={rs} category={categoryBySkill[rs.skill]} />
              ))}
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-400">
            No specific technical skills were extracted — try pasting a more detailed job description.
          </p>
        )}

        {preferred.length > 0 && (
          <div className="flex flex-col gap-2">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Preferred</p>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {preferred.map((rs) => (
                <SkillChip key={rs.skill} skill={rs} category={categoryBySkill[rs.skill]} />
              ))}
            </div>
          </div>
        )}
      </Card>

      {job.soft_skills.length > 0 && (
        <Card className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-sky-50 text-sky-600">
              <MessageCircle size={16} />
            </span>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Soft Skills</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {job.soft_skills.map((skill) => (
              <Badge key={skill} tone="info">
                {skill}
              </Badge>
            ))}
          </div>
        </Card>
      )}

      {job.tools.length > 0 && (
        <Card className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-100 text-slate-600">
              <Wrench size={16} />
            </span>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Tools</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {job.tools.map((tool) => (
              <Badge key={tool} tone="neutral">
                {tool}
              </Badge>
            ))}
          </div>
        </Card>
      )}

      {job.experience_years !== null && (
        <Card padding="sm" className="flex items-center gap-3 border-slate-100 bg-slate-50/60">
          <Briefcase size={16} className="text-slate-400" />
          <p className="text-sm text-slate-600">
            <span className="font-medium text-slate-800">{job.experience_years}+ years</span> of experience preferred
          </p>
        </Card>
      )}

      <LinkButton href="/evidence" icon={<ArrowRight size={16} />} className="flex-row-reverse self-start">
        Continue to Candidate Evidence
      </LinkButton>
    </div>
  );
}
