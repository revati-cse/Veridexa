"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useSessionStore } from "@/lib/store";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";

export default function JobPage() {
  const router = useRouter();
  const setJob = useSessionStore((s) => s.setJob);
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    <div className="flex flex-col gap-4">
      <h2 className="text-2xl font-semibold">Job Description</h2>
      <p className="text-slate-600">Paste the job description below and Veridexa will extract the required skills.</p>
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Paste a job description (e.g. Data Analyst)..."
        rows={10}
        className="rounded-md border border-slate-300 p-3 font-mono text-sm"
      />
      {error && <ErrorState message={error} onRetry={handleAnalyze} />}
      {loading && <LoadingState label="Analyzing job description..." />}
      <button
        onClick={handleAnalyze}
        disabled={loading || description.trim().length < 20}
        className="self-start rounded-md bg-slate-900 px-5 py-2.5 font-medium text-white hover:bg-slate-700 disabled:opacity-40"
      >
        Analyze Job
      </button>
    </div>
  );
}
