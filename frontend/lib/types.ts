/**
 * Mirrors backend/app/schemas/*.py exactly. Frozen contract between the two
 * devs (BLUEPRINT.md checklist item 4) — if a Pydantic model changes, update
 * this file in the same commit. Do not let these drift independently.
 */

// ---------------------------------------------------------------------------
// common.py
// ---------------------------------------------------------------------------

export type Importance = "high" | "medium" | "low";

export type SkillCategory =
  | "programming"
  | "database"
  | "data"
  | "ai_ml"
  | "cloud"
  | "business"
  | "communication"
  | "problem_solving"
  | "tools";

export type EvidenceStrength = "none" | "weak" | "moderate" | "strong";

export type EvidenceSourceType =
  | "resume"
  | "project"
  | "github"
  | "challenge"
  | "submission";

export type ClaimLevel = "beginner" | "intermediate" | "advanced";

export type Difficulty = 1 | 2 | 3;

// ---------------------------------------------------------------------------
// skill.py
// ---------------------------------------------------------------------------

export interface SkillTaxonomyItem {
  id: string; // uuid
  name: string;
  category: SkillCategory;
}

export interface ClaimedSkill {
  skill: string;
  level: ClaimLevel;
}

export interface ClaimsRequest {
  user_id: string;
  claims: ClaimedSkill[];
}

// ---------------------------------------------------------------------------
// job.py
// ---------------------------------------------------------------------------

export interface JobRequiredSkill {
  skill: string;
  importance: Importance;
  required: boolean;
}

export interface JobParseRequest {
  raw_description: string;
}

export interface ParsedJob {
  title: string;
  required_skills: JobRequiredSkill[];
  soft_skills: string[];
  tools: string[];
  experience_years: number | null;
}

export interface JobParseResponse {
  job_id: string;
  job: ParsedJob;
  demo_fallback: boolean;
}

// ---------------------------------------------------------------------------
// github.py
// ---------------------------------------------------------------------------

export interface GithubAnalyzeRequest {
  user_id: string;
  repository_url: string;
  claimed_skills: ClaimedSkill[]; // levels matter for claims_vs_evidence, not just names
  required_skills: string[];
}

export interface LanguageDetected {
  language: string;
  confidence: number; // 0-1
}

export interface SkillEvidenceItem {
  skill: string;
  evidence_strength: EvidenceStrength;
  confidence: number; // 0-1
  observations: string[];
}

export interface ClaimVsEvidenceItem {
  skill: string;
  claim: ClaimLevel | null;
  repository_evidence: EvidenceStrength;
  assessment: string;
}

export interface GithubAnalyzeResponse {
  repository_id: string;
  repository: string;
  languages_detected: LanguageDetected[];
  skills: SkillEvidenceItem[];
  claims_vs_evidence: ClaimVsEvidenceItem[];
  demo_fallback: boolean;
  // Set server-side (ISO 8601). freshness_engine.py's only signal for this
  // source — round-trips unchanged once passed back into a later request.
  analyzed_at: string;
}

// ---------------------------------------------------------------------------
// challenge.py
// ---------------------------------------------------------------------------

export interface ChallengeGenerateRequest {
  job_id: string;
  // No DB persistence yet — passed from the session store rather than
  // looked up backend-side by job_id.
  job_title: string;
  user_id: string;
  required_skills: string[];
  difficulty: Difficulty;
}

export interface Challenge {
  id: string;
  job_id: string | null;
  parent_challenge_id: string | null;
  title: string;
  role: string;
  scenario: string;
  instructions: string;
  required_skills: string[];
  difficulty: Difficulty;
  dataset: unknown; // shape interpreted by the SQL sandbox, not the UI
  expected_output: string | null;
  evaluation_criteria: Record<string, number>; // criterion -> weight, sums to 1
  mutation_reason: string | null;
}

export interface ChallengeGenerateResponse {
  challenge: Challenge;
  demo_fallback: boolean;
}

/** No DB persistence yet — the frontend already holds the full previous
 * Challenge + its evaluation (as a SubmissionRecord) from the screens it
 * already passed through, sent directly rather than by id. */
export interface ChallengeMutateRequest {
  user_id: string;
  job_id: string;
  job_title: string;
  required_skills: string[];
  previous_attempt: SubmissionRecord;
}

export interface ChallengeMutateResponse {
  challenge: Challenge;
  demo_fallback: boolean;
}

export interface ChallengeHistoryResponse {
  chain: Challenge[]; // oldest first
}

// ---------------------------------------------------------------------------
// submission.py
// ---------------------------------------------------------------------------

export interface SubmissionCreate {
  // No DB persistence yet — the full challenge (already held in the session
  // store) is sent directly rather than looked up backend-side by id.
  challenge: Challenge;
  user_id: string;
  code: string;
  explanation: string;
}

// ---------------------------------------------------------------------------
// evaluation.py
// ---------------------------------------------------------------------------

export interface SqlExecutionResult {
  success: boolean;
  columns: string[];
  rows: unknown[][];
  row_count: number;
  error: string | null;
  rejected_reason: string | null;
}

export interface EvidenceObservation {
  skill: string;
  observation: string;
  confidence: number; // 0-1
}

export interface SkillGapItem {
  skill: string;
  missing_concepts: string[];
}

export interface SubmissionEvaluationResponse {
  submission_id: string;
  evaluation_id: string;
  rubric_scores: Record<string, number>; // criterion -> 0-100
  overall_score: number; // 0-100, backend-computed weighted sum
  strengths: string[];
  weaknesses: string[];
  evidence: EvidenceObservation[];
  skill_gaps: SkillGapItem[];
  sql_execution_result: SqlExecutionResult | null;
  demo_fallback: boolean;
  // Set server-side (ISO 8601). freshness_engine.py's only signal for this
  // source — round-trips unchanged once passed back into a later request.
  evaluated_at: string;
}

/** One completed challenge attempt. No DB persistence yet — the frontend
 * accumulates these in the session store (see store.ts) and passes the full
 * history to evidence_engine / readiness_engine, e.g. so a mutated
 * challenge's improved score is reflected in readiness. */
export interface SubmissionRecord {
  challenge: Challenge;
  evaluation: SubmissionEvaluationResponse;
}

// ---------------------------------------------------------------------------
// evidence.py
// ---------------------------------------------------------------------------

export interface EvidenceItem {
  id: string;
  skill: string;
  source_type: EvidenceSourceType;
  source_reference: string | null;
  observation: string;
  confidence: number; // 0-1
  created_at: string; // ISO datetime
}

export interface SkillEvidenceGroup {
  skill: string;
  evidence: EvidenceItem[]; // never render a % with an empty list — show "Not yet assessed"
}

/** No DB persistence yet, so evidence is computed directly from session
 * state rather than looked up by user_id. Deliberately carries no `claims`
 * field — a claim is not evidence (Section 2). */
export interface EvidenceComputeRequest {
  user_id: string;
  github_evidence: GithubAnalyzeResponse | null;
  submission_history: SubmissionRecord[];
}

export interface EvidenceListResponse {
  user_id: string;
  skills: SkillEvidenceGroup[];
}

// ---------------------------------------------------------------------------
// readiness.py
// ---------------------------------------------------------------------------

export interface SkillScoreBreakdown {
  skill: string;
  importance: Importance;
  importance_weight: number; // high=3, medium=2, low=1
  score: number; // 0-100
  weighted_contribution: number;
}

/** No DB persistence yet, so readiness is computed directly from session
 * state (already held for the job/evidence/challenge screens) rather than
 * looked up by job_id. */
export interface ReadinessComputeRequest {
  user_id: string;
  job_id: string;
  job_title: string;
  required_skills: JobRequiredSkill[];
  claims: ClaimedSkill[];
  github_evidence: GithubAnalyzeResponse | null;
  submission_history: SubmissionRecord[];
}

export interface ReadinessResponse {
  user_id: string;
  job_id: string;
  job_title: string;
  readiness_score: number; // 0-100
  skill_breakdown: SkillScoreBreakdown[];
  strengths: string[];
  weaknesses: string[];
  skill_gaps: SkillGapItem[];
}

// ---------------------------------------------------------------------------
// freshness.py (P2/optional — see freshness_engine.py)
// ---------------------------------------------------------------------------

export type FreshnessLabel = "fresh" | "aging" | "stale" | "not_assessed";

/** Informational only — does NOT feed into ReadinessResponse.skill_breakdown
 * scores. "How confident are we" (readiness) and "how current is that
 * confidence" (this) are deliberately separate questions. */
export interface SkillFreshnessItem {
  skill: string;
  last_evidence_at: string | null; // ISO 8601
  days_since_last_evidence: number | null;
  freshness: FreshnessLabel;
}

export interface FreshnessComputeRequest {
  user_id: string;
  required_skills: JobRequiredSkill[];
  github_evidence: GithubAnalyzeResponse | null;
  submission_history: SubmissionRecord[];
}

export interface FreshnessResponse {
  user_id: string;
  skills: SkillFreshnessItem[];
}

// ---------------------------------------------------------------------------
// recruiter.py (P3/optional — see recruiter_dashboard.py)
// ---------------------------------------------------------------------------

/** readiness_score here is computed by the exact same formula as
 * ReadinessResponse.readiness_score, from persisted challenge/evaluation
 * history — never a separately-derived recruiter-side number. Computed
 * without claims or GitHub evidence (neither is persisted anywhere yet),
 * so it reflects challenge performance only. skill_breakdown is the same
 * per-skill rows compute_readiness produces — the candidate-comparison
 * view on /recruiter is built directly from this, no second endpoint. */
export interface CandidateSummary {
  user_id: string;
  readiness_score: number; // 0-100
  challenges_completed: number;
  strengths: string[];
  weaknesses: string[];
  skill_gaps: SkillGapItem[];
  skill_breakdown: SkillScoreBreakdown[];
}

/** The one response in this API that requires a database — there's no
 * "compute from session state" fallback for "which candidates applied to
 * this job" (that spans multiple candidates' sessions). db_available: false
 * means the dashboard is empty because no database is configured, not
 * because no one has applied yet — show that distinction to the user. */
export interface RecruiterDashboardResponse {
  job_id: string;
  job_title: string;
  db_available: boolean;
  candidates: CandidateSummary[];
}
