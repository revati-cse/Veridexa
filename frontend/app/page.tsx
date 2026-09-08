import { Fragment } from "react";
import Link from "next/link";
import {
  ArrowRight,
  FileText,
  ListChecks,
  FolderGit2,
  Code2,
  Sparkles,
  Gauge,
  X,
  CheckCircle2,
  Github,
  RefreshCw,
  BarChart3,
} from "lucide-react";
import { LinkButton } from "@/components/shared/Button";
import { Card } from "@/components/shared/Card";
import { Logo } from "@/components/layout/Logo";

const PIPELINE = [
  { icon: FileText, label: "Job Description" },
  { icon: ListChecks, label: "Required Skills" },
  { icon: FolderGit2, label: "Candidate Evidence" },
  { icon: Code2, label: "Real-World Challenge" },
  { icon: Sparkles, label: "AI Evaluation" },
  { icon: Gauge, label: "Job Readiness" },
];

const HIGHLIGHTS = [
  { icon: Github, title: "GitHub Evidence", body: "Real repositories analyzed read-only for skills actually used." },
  { icon: Code2, title: "Real-World Challenges", body: "A live task built from the job's own top skills — not a quiz." },
  { icon: BarChart3, title: "Evidence-Based Skill Scores", body: "Every score traces to code that ran or work that was graded." },
  { icon: RefreshCw, title: "Adaptive Challenge Mutation", body: "The next challenge targets exactly what you got wrong." },
];

export default function LandingPage() {
  return (
    <div className="flex flex-col gap-20 py-6 sm:gap-28 sm:py-10">
      {/* Hero */}
      <section className="flex flex-col items-center gap-6 text-center">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700 ring-1 ring-inset ring-indigo-600/20">
          <Sparkles size={12} />
          Evidence-based skill verification
        </span>

        <Logo size="lg" />

        <p className="max-w-xl text-xl font-medium text-slate-700 sm:text-2xl">
          &ldquo;From claimed skills to proven capability.&rdquo;
        </p>

        <p className="max-w-2xl text-balance text-slate-600">
          Analyze job requirements, inspect real project evidence, simulate real-world work, and measure job
          readiness.
        </p>

        <div className="mt-2 flex flex-wrap items-center justify-center gap-3">
          <LinkButton href="/job" icon={<ArrowRight size={16} />} className="flex-row-reverse">
            Analyze a Job
          </LinkButton>
          <LinkButton href="#how-it-works" variant="secondary">
            See How It Works
          </LinkButton>
        </div>
      </section>

      {/* Pipeline */}
      <section id="how-it-works" className="scroll-mt-24">
        <div className="mb-8 flex flex-col items-center gap-2 text-center">
          <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">The Veridexa Pipeline</p>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">One continuous loop</h2>
        </div>

        <div className="flex flex-col gap-2 lg:flex-row lg:items-center">
          {PIPELINE.map(({ icon: Icon, label }, i) => (
            <Fragment key={label}>
              <Card padding="sm" className="flex flex-col items-center gap-2 text-center lg:flex-1">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-indigo-50 text-indigo-600">
                  <Icon size={18} />
                </span>
                <p className="text-sm font-semibold text-slate-800">{label}</p>
              </Card>
              {i < PIPELINE.length - 1 && (
                <div className="flex justify-center py-0.5 lg:px-0.5 lg:py-0">
                  <ArrowRight size={16} className="shrink-0 rotate-90 text-slate-300 lg:rotate-0" aria-hidden />
                </div>
              )}
            </Fragment>
          ))}
        </div>
      </section>

      {/* Why Veridexa */}
      <section className="flex flex-col gap-10">
        <div className="flex flex-col items-center gap-2 text-center">
          <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">Why Veridexa?</p>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            Claims are not enough. Evidence matters.
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Card className="flex flex-col gap-3 border-slate-200 bg-slate-50/60">
            <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-slate-200/80 px-2.5 py-0.5 text-xs font-semibold text-slate-600">
              <X size={12} />
              Resume Claims
            </span>
            <p className="text-2xl font-bold text-slate-500">&ldquo;I know SQL.&rdquo;</p>
            <p className="text-sm text-slate-500">
              What a resume or profile says. Unverifiable, and every candidate writes the same words.
            </p>
          </Card>
          <Card className="flex flex-col gap-3 border-indigo-200 bg-indigo-50/60">
            <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-indigo-600 px-2.5 py-0.5 text-xs font-semibold text-white">
              <CheckCircle2 size={12} />
              Demonstrated Evidence
            </span>
            <p className="text-2xl font-bold text-indigo-900">A graded, real-world challenge.</p>
            <p className="text-sm text-indigo-800">
              Built from the job itself, solved live, executed for real. This is the only thing Veridexa trusts.
            </p>
          </Card>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {HIGHLIGHTS.map(({ icon: Icon, title, body }) => (
            <Card key={title} padding="sm" className="flex flex-col gap-2">
              <span className="grid h-9 w-9 place-items-center rounded-lg bg-indigo-50 text-indigo-600">
                <Icon size={16} />
              </span>
              <p className="text-sm font-semibold text-slate-900">{title}</p>
              <p className="text-xs leading-relaxed text-slate-500">{body}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Closing CTA */}
      <section>
        <Card padding="lg" className="flex flex-col items-center gap-4 border-indigo-200 bg-indigo-600 text-center">
          <h2 className="text-2xl font-bold text-white sm:text-3xl">Ready to prove it?</h2>
          <p className="max-w-lg text-indigo-100">
            Paste a job description and see exactly what skills matter — then let Veridexa build the evidence.
          </p>
          <Link
            href="/job"
            className="inline-flex items-center gap-2 rounded-lg bg-white px-6 py-3 text-sm font-semibold text-indigo-700 shadow-sm transition-colors hover:bg-indigo-50"
          >
            Analyze a Job
            <ArrowRight size={16} />
          </Link>
        </Card>
      </section>
    </div>
  );
}
