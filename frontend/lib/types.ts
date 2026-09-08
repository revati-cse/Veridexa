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

export interface ChallengeMutateRequest {
  previous_challenge_id: string;
  evaluation_id: string;
  user_id: string;
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
