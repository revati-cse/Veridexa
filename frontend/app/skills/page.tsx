"use client";

import Link from "next/link";
import { useSessionStore } from "@/lib/store";
import { EmptyState } from "@/components/shared/EmptyState";

const IMPORTANCE_STYLE: Record<string, string> = {
  high: "bg-red-100 text-red-800",
  medium: "bg-amber-100 text-amber-800",
  low: "bg-slate-100 text-slate-700",
};

export default function SkillsPage() {
  const jobId = useSessionStore((s) => s.jobId);
  const job = useSessionStore((s) => s.job);

  if (!job) {
    return (
      <EmptyState
        message="No job analyzed yet."
        action={
          <Link href="/job" className="text-slate-900 underline">
            Go analyze a job description
          </Link>
        }
      />
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-2xl font-semibold">{job.title}</h2>
      <p className="text-slate-600">Required skills extracted from the job description.</p>
      {jobId && (
        <p className="text-xs text-slate-400">
          Job ID: <span className="font-mono">{jobId}</span> — recruiters can look up this job&apos;s candidates at{" "}
          <span className="font-mono">/recruiter</span>.
        </p>
      )}
      {job.required_skills.length > 0 ? (
        <ul className="flex flex-col gap-2">
          {job.required_skills.map((rs) => (
            <li
              key={rs.skill}
              className="flex items-center justify-between rounded-md border border-slate-200 bg-white px-4 py-2.5"
            >
              <span className="font-medium">{rs.skill}</span>
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${IMPORTANCE_STYLE[rs.importance]}`}>
                {rs.importance}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-slate-400">
          No specific technical skills were extracted — try pasting a more detailed job description.
        </p>
      )}
      {job.tools.length > 0 && (
        <p className="text-sm text-slate-500">Tools: {job.tools.join(", ")}</p>
      )}
      <Link
        href="/evidence"
        className="mt-2 self-start rounded-md bg-slate-900 px-5 py-2.5 font-medium text-white hover:bg-slate-700"
      >
        Continue to Candidate Evidence
      </Link>
    </div>
  );
}
