import Link from "next/link";
import {
  ArrowRight,
  FileText,
  ListChecks,
  FolderGit2,
  Code2,
  Sparkles,
  Gauge,
  Github,
  RefreshCw,
  BarChart3,
  ShieldCheck,
} from "lucide-react";
import { LinkButton } from "@/components/shared/Button";
import { Card } from "@/components/shared/Card";
import { Badge } from "@/components/shared/Badge";
import { Logo } from "@/components/layout/Logo";
import { ScoreRing } from "@/components/shared/ScoreRing";
import { ProgressBar } from "@/components/shared/ProgressBar";

const PIPELINE = [
  {
    icon: FileText,
    label: "Job Description",
    desc: "Paste any real posting — Veridexa reads it for the skills that actually matter.",
  },
  {
    icon: ListChecks,
    label: "Required Skills",
    desc: "Extracted and ranked by importance, not just keyword-matched.",
  },
  {
    icon: FolderGit2,
    label: "Candidate Evidence",
    desc: "Claimed skills, optionally backed by a real GitHub repository read read-only.",
  },
  {
    icon: Code2,
    label: "Real-World Challenge",
    desc: "A live SQL task generated from the job's own top skills — not a quiz bank.",
  },
  {
    icon: Sparkles,
    label: "AI Evaluation",
    desc: "The query runs for real first. AI reasons over what actually happened.",
  },
  {
    icon: Gauge,
    label: "Job Readiness",
    desc: "A deterministic score, computed by the backend — never guessed by the model.",
  },
];

const HIGHLIGHTS = [
  {
    icon: RefreshCw,
    title: "Adaptive Challenge Mutation",
    body: "Miss a rubric criterion and Veridexa doesn't just re-grade — it mutates a new challenge that targets exactly what you got wrong, then lets you prove you fixed it.",
    featured: true,
  },
  {
    icon: Github,
    title: "GitHub Evidence",
    body: "Real repositories, read-only — skills you've actually used, not skills you listed.",
  },
  {
    icon: Code2,
    title: "Real-World Challenges",
    body: "A live task built from the job's own top skills.",
  },
  {
    icon: BarChart3,
    title: "Evidence-Based Scores",
    body: "Every score traces back to code that ran or work that was graded.",
  },
];

export default function LandingPage() {
  return (
    <div className="flex flex-col gap-24 pb-16 sm:gap-32">
      {/* Hero */}
      <section className="bg-noise relative -mx-4 overflow-hidden rounded-b-[2.5rem] bg-gradient-to-br from-indigo-950 via-indigo-900 to-slate-900 px-4 pb-16 pt-10 sm:-mx-6 sm:rounded-b-[3rem] sm:px-10 sm:pb-24 sm:pt-14 lg:px-16">
        <div
          className="pointer-events-none absolute -right-24 -top-24 h-96 w-96 rounded-full opacity-40 blur-3xl"
          style={{ background: "radial-gradient(circle, rgba(244,86,42,0.55), transparent 70%)" }}
          aria-hidden
        />
        <div
          className="pointer-events-none absolute -bottom-32 left-1/3 h-80 w-80 rounded-full opacity-30 blur-3xl"
          style={{ background: "radial-gradient(circle, rgba(99,102,241,0.6), transparent 70%)" }}
          aria-hidden
        />

        <div className="relative mx-auto flex max-w-6xl flex-col gap-12 lg:flex-row lg:items-center lg:gap-8">
          <div className="flex flex-col gap-6 lg:flex-1">
            <Logo size="md" />

            <div className="flex flex-col gap-4">
              <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-indigo-100 ring-1 ring-inset ring-white/20">
                <Sparkles size={12} />
                Evidence-based skill verification
              </span>
              <h1 className="max-w-xl font-display text-4xl italic leading-[1.1] text-white sm:text-5xl">
                From claimed skills to proven capability.
              </h1>
              <p className="max-w-md text-balance text-indigo-100/80">
                Paste a job description, back up your claims with real work, and let Veridexa run the
                evidence — a live challenge, graded for real, not a survey about your résumé.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <LinkButton href="/job" icon={<ArrowRight size={16} />} className="flex-row-reverse">
                Analyze a Job
              </LinkButton>
              <Link
                href="#how-it-works"
                className="inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-indigo-100 transition-colors hover:text-white"
              >
                See how it works
              </Link>
            </div>
          </div>

          {/* Product preview — a real composition of the same components the
              app uses on the Readiness screen, not a stock illustration. */}
          <div className="lg:max-w-sm lg:flex-1">
            <Card padding="lg" className="rotate-1 border-white/10 shadow-soft-lg transition-transform hover:rotate-0">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">Preview</p>
                <Badge tone="brand">Illustrative</Badge>
              </div>
              <div className="mt-4 flex items-center gap-5">
                <ScoreRing value={82} label="Readiness" size={104} />
                <div>
                  <p className="font-display text-lg font-semibold text-slate-900">Data Analyst</p>
                  <p className="text-sm text-slate-500">2 challenges completed</p>
                </div>
              </div>
              <div className="mt-5 flex flex-col gap-2.5 border-t border-slate-100 pt-4">
                <ProgressBar label="SQL" value={91} />
                <ProgressBar label="Statistics" value={78} />
                <ProgressBar label="Communication" value={65} />
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* Pipeline */}
      <section id="how-it-works" className="mx-auto w-full max-w-2xl scroll-mt-24 px-1">
        <div className="mb-10 flex flex-col gap-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">The Veridexa Pipeline</p>
          <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            One continuous loop
          </h2>
        </div>

        <ol className="flex flex-col">
          {PIPELINE.map(({ icon: Icon, label, desc }, i) => (
            <li key={label} className="relative flex gap-5 pb-9 last:pb-0">
              {i < PIPELINE.length - 1 && (
                <span className="absolute left-[19px] top-11 h-full w-px bg-slate-200" aria-hidden />
              )}
              <span className="relative z-10 grid h-10 w-10 shrink-0 place-items-center rounded-full border border-indigo-200 bg-white font-display text-sm font-semibold text-indigo-600">
                {i + 1}
              </span>
              <div className="flex flex-1 items-start justify-between gap-4 pt-1.5">
                <div>
                  <p className="font-display text-base font-semibold text-slate-900">{label}</p>
                  <p className="mt-1 max-w-md text-sm text-slate-500">{desc}</p>
                </div>
                <Icon size={20} className="mt-0.5 hidden shrink-0 text-indigo-300 sm:block" />
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* Why Veridexa — editorial split, not matching cards */}
      <section className="mx-auto w-full max-w-5xl px-1">
        <div className="mb-10 flex flex-col gap-2 text-center">
          <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">Why Veridexa?</p>
          <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            Claims are not enough. Evidence matters.
          </h2>
        </div>

        <div className="grid grid-cols-1 items-center gap-10 lg:grid-cols-2 lg:gap-16">
          <div className="flex flex-col gap-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">What a resume says</p>
            <p className="font-display text-3xl italic leading-tight text-slate-400 line-through decoration-slate-300 decoration-2 sm:text-4xl">
              &ldquo;I know SQL.&rdquo;
            </p>
            <p className="max-w-sm text-sm text-slate-500">
              Unverifiable, and every candidate writes the same words. Nothing here traces back to work
              that actually happened.
            </p>
          </div>

          <Card padding="lg" className="border-indigo-100 bg-indigo-50/40">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-600 px-2.5 py-1 text-xs font-semibold text-white">
              <ShieldCheck size={12} />
              What Veridexa trusts
            </span>
            <p className="mt-3 font-display text-xl font-semibold text-indigo-950">
              A graded, real-world challenge — built from the job itself, solved live, executed for real.
            </p>
            <div className="mt-4 flex flex-col gap-2.5 border-t border-indigo-100 pt-4">
              <ProgressBar label="Correctness" value={94} />
              <ProgressBar label="Reasoning" value={88} />
              <ProgressBar label="Edge Cases" value={76} />
            </div>
          </Card>
        </div>

        {/* Highlights — one featured item, three supporting, instead of four
            identical cards. */}
        <div className="mt-14 grid grid-cols-1 gap-4 md:grid-cols-3 md:grid-rows-2">
          {HIGHLIGHTS.map(({ icon: Icon, title, body, featured }) => (
            <Card
              key={title}
              padding="lg"
              className={
                featured
                  ? "relative flex flex-col justify-between gap-4 overflow-hidden border-indigo-200 bg-gradient-to-br from-indigo-600 to-indigo-800 text-white md:col-span-2 md:row-span-2"
                  : "flex flex-col gap-2.5"
              }
            >
              {featured && (
                <Icon size={220} strokeWidth={1} className="pointer-events-none absolute -bottom-10 -right-10 text-white/10" aria-hidden />
              )}
              <span
                className={
                  featured
                    ? "relative grid h-10 w-10 place-items-center rounded-lg bg-white/15 text-white"
                    : "grid h-9 w-9 place-items-center rounded-lg bg-indigo-50 text-indigo-600"
                }
              >
                <Icon size={featured ? 20 : 16} />
              </span>
              <div className="relative">
                <p className={featured ? "font-display text-xl font-semibold" : "text-sm font-semibold text-slate-900"}>
                  {title}
                </p>
                <p className={featured ? "mt-2 max-w-sm text-sm leading-relaxed text-indigo-100" : "mt-1 text-xs leading-relaxed text-slate-500"}>
                  {body}
                </p>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Closing CTA */}
      <section className="mx-auto w-full max-w-5xl px-1">
        <Card
          padding="lg"
          className="bg-noise relative overflow-hidden border-none bg-gradient-to-br from-ember-600 to-ember-800 text-center"
        >
          <div className="relative flex flex-col items-center gap-4">
            <h2 className="font-display text-2xl font-semibold text-white sm:text-3xl">Ready to prove it?</h2>
            <p className="max-w-lg text-ember-50/90">
              Paste a job description and see exactly what skills matter — then let Veridexa build the
              evidence.
            </p>
            <Link
              href="/job"
              className="inline-flex items-center gap-2 rounded-lg bg-white px-6 py-3 text-sm font-semibold text-ember-700 shadow-soft transition-colors hover:bg-ember-50"
            >
              Analyze a Job
              <ArrowRight size={16} />
            </Link>
          </div>
        </Card>
      </section>
    </div>
  );
}
