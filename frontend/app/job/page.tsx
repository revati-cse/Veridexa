"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Sparkles, Wand2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useSessionStore } from "@/lib/store";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";
import { Card } from "@/components/shared/Card";
import { Button } from "@/components/shared/Button";
import { PageHeader } from "@/components/shared/PageHeader";

const MIN_LENGTH = 20;

const EXAMPLE_JD =
  "We are hiring a Data Analyst to join our growing analytics team. The ideal candidate has strong " +
  "SQL and Python skills, is comfortable with statistics (hypothesis testing, significance), and can " +
  "build dashboards in Power BI. Strong problem-solving skills required. 2+ years of experience preferred.";

export default function JobPage() {
  const router = useRouter();
  const setJob = useSessionStore((s) => s.setJob);
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trimmedLength = description.trim().length;
  const isTooShort = trimmedLength > 0 && trimmedLength < MIN_LENGTH;
  const canAnalyze = trimmedLength >= MIN_LENGTH && !loading;

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.parseJob({ raw_description: description });
      setJob(res.job_id, res.job);
      router.push("/skills");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to analyze the job description.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <PageHeader
        eyebrow="Step 1 of 6"
        title="Discover what skills actually matter"
        subtitle="Paste a real job description below. Veridexa extracts the exact, ranked skills this role is graded against — not a keyword match."
      />

      <Card className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <label htmlFor="jd" className="text-sm font-semibold text-slate-700">
              Job Description
            </label>
            <button
              type="button"
              onClick={() => setDescription(EXAMPLE_JD)}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-indigo-600 hover:text-indigo-700"
            >
              <Wand2 size={13} />
              Try a Data Analyst role
            </button>
          </div>
          <textarea
            id="jd"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Paste the full job posting — responsibilities, required skills, tools, and experience level all help Veridexa extract a more accurate skill profile."
            rows={12}
            aria-describedby="jd-hint"
            className="rounded-lg border border-slate-300 p-3.5 font-mono text-sm leading-relaxed text-slate-800 shadow-inner focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          />
          <div className="flex items-center justify-between text-xs">
            <p id="jd-hint" className={isTooShort ? "font-medium text-amber-600" : "text-slate-400"}>
              {isTooShort
                ? `Add ${MIN_LENGTH - trimmedLength} more characters for a reliable analysis.`
                : "A few sentences on responsibilities and required skills works well."}
            </p>
            <p className="text-slate-400">{trimmedLength} characters</p>
          </div>
        </div>

        {error && <ErrorState message={error} onRetry={handleAnalyze} />}
        {loading && <LoadingState label="Analyzing job description..." />}

        <Button
          onClick={handleAnalyze}
          disabled={!canAnalyze}
          icon={<ArrowRight size={16} />}
          className="flex-row-reverse self-start"
        >
          Analyze Job
        </Button>
      </Card>

      <Card padding="sm" className="flex items-start gap-3 border-indigo-100 bg-indigo-50/60">
        <Sparkles size={16} className="mt-0.5 shrink-0 text-indigo-500" />
        <p className="text-xs leading-relaxed text-indigo-800">
          Every job also gets an ID a recruiter can look up later on the Recruiter View, once this job&apos;s
          candidates have completed a challenge.
        </p>
      </Card>
    </div>
  );
}
