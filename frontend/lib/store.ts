import { create } from "zustand";
import type {
  Challenge,
  ClaimedSkill,
  GithubAnalyzeResponse,
  ParsedJob,
  ProjectDescriptionAnalyzeResponse,
  ReadinessResponse,
  SubmissionEvaluationResponse,
  SubmissionRecord,
} from "./types";

/**
 * Single in-memory session store per BLUEPRINT.md Section D. No persistence
 * beyond the candidate id (lib/candidateId.ts) — the demo flow is linear
 * within one sitting, so a page refresh mid-flow resetting state is an
 * accepted tradeoff at this stage, not a bug to fix yet.
 *
 * submissionHistory accumulates every completed challenge attempt
 * (oldest-first) — evidence_engine and readiness_engine both need the full
 * history, not just the latest evaluation, since there's no DB to query it
 * from and a mutated challenge's improved score must still reflect the
 * skill's earlier, weaker attempt too.
 */
interface SessionState {
  jobId: string | null;
  job: ParsedJob | null;
  claims: ClaimedSkill[];
  githubEvidence: GithubAnalyzeResponse | null;
  projectDescriptionEvidence: ProjectDescriptionAnalyzeResponse | null;
  currentChallenge: Challenge | null;
  evaluation: SubmissionEvaluationResponse | null;
  submissionHistory: SubmissionRecord[];
  readiness: ReadinessResponse | null;

  setJob: (jobId: string, job: ParsedJob) => void;
  setClaims: (claims: ClaimedSkill[]) => void;
  setGithubEvidence: (evidence: GithubAnalyzeResponse | null) => void;
  setProjectDescriptionEvidence: (evidence: ProjectDescriptionAnalyzeResponse | null) => void;
  setCurrentChallenge: (challenge: Challenge) => void;
  setEvaluation: (evaluation: SubmissionEvaluationResponse) => void;
  addSubmissionRecord: (challenge: Challenge, evaluation: SubmissionEvaluationResponse) => void;
  setReadiness: (readiness: ReadinessResponse) => void;
  reset: () => void;
}

const initialState = {
  jobId: null,
  job: null,
  claims: [],
  githubEvidence: null,
  projectDescriptionEvidence: null,
  currentChallenge: null,
  evaluation: null,
  submissionHistory: [],
  readiness: null,
} satisfies Partial<SessionState>;

export const useSessionStore = create<SessionState>((set) => ({
  ...initialState,
  setJob: (jobId, job) => set({ jobId, job }),
  setClaims: (claims) => set({ claims }),
  setGithubEvidence: (githubEvidence) => set({ githubEvidence }),
  setProjectDescriptionEvidence: (projectDescriptionEvidence) => set({ projectDescriptionEvidence }),
  setCurrentChallenge: (currentChallenge) => set({ currentChallenge }),
  setEvaluation: (evaluation) => set({ evaluation }),
  addSubmissionRecord: (challenge, evaluation) =>
    set((state) => ({ submissionHistory: [...state.submissionHistory, { challenge, evaluation }] })),
  setReadiness: (readiness) => set({ readiness }),
  reset: () => set(initialState),
}));
