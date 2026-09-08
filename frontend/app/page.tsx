import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="flex flex-col items-center gap-6 py-24 text-center">
      <h1 className="text-4xl font-bold tracking-tight">VERIDEXA AI</h1>
      <p className="text-lg text-slate-600">&ldquo;From claimed skills to proven capability.&rdquo;</p>
      <Link
        href="/job"
        className="mt-4 rounded-md bg-slate-900 px-6 py-3 font-medium text-white hover:bg-slate-700"
      >
        Assess My Job Readiness
      </Link>
    </div>
  );
}
