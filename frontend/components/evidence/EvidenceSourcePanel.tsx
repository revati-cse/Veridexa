import type { ReactNode } from "react";
import { MessageSquareText, ShieldCheck } from "lucide-react";
import { Card } from "@/components/shared/Card";
import { Badge, type BadgeTone } from "@/components/shared/Badge";
import { ProgressBar } from "@/components/shared/ProgressBar";
import type { ClaimVsEvidenceItem, EvidenceStrength, SkillEvidenceItem } from "@/lib/types";

const STRENGTH_TONE: Record<EvidenceStrength, BadgeTone> = {
  strong: "success",
  moderate: "info",
  weak: "warning",
  none: "neutral",
};

/** Shared render for any evidence source shaped like GithubAnalyzeResponse /
 * ProjectDescriptionAnalyzeResponse (skills + claims_vs_evidence +
 * demo_fallback) — the evidence page shows one of these per source instead
 * of duplicating the skill-card/claim-table JSX for each. */
export function EvidenceSourcePanel({
  header,
  skills,
  claimsVsEvidence,
  demoFallback,
}: {
  header: ReactNode;
  skills: SkillEvidenceItem[];
  claimsVsEvidence: ClaimVsEvidenceItem[];
  demoFallback: boolean;
}) {
  return (
    <div className="flex flex-col gap-4">
      <Card className="flex flex-col gap-3 border-indigo-100">
        <div className="flex flex-wrap items-center justify-between gap-2">
          {header}
          {demoFallback && <Badge tone="neutral">Demo fallback</Badge>}
        </div>
      </Card>

      {skills.length > 0 && (
        <div className="flex flex-col gap-3">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <ShieldCheck size={15} className="text-emerald-600" />
            Skills demonstrated
          </h3>
          {skills.map((s) => (
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

      {claimsVsEvidence.length > 0 && (
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
                {claimsVsEvidence.map((row) => (
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
  );
}
