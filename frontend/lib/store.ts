import { create } from "zustand";
import type {
  Challenge,
  ClaimedSkill,
  GithubAnalyzeResponse,
  ParsedJob,
  ReadinessResponse,
  SubmissionEvaluationResponse,
} from "./types";

/**
 * Single in-memory session store per BLUEPRINT.md Section D. No persistence
 * beyond the candidate id (lib/candidateId.ts) — the demo flow is linear
 * within one sitting, so a page refresh mid-flow resetting state is an
 * accepted tradeoff at this stage, not a bug to fix yet.
 */
interface SessionState {
  jobId: string | null;
  job: ParsedJob | null;
  claims: ClaimedSkill[];
  githubEvidence: GithubAnalyzeResponse | null;
  currentChallenge: Challenge | null;
  evaluation: SubmissionEvaluationResponse | null;
  readiness: ReadinessResponse | null;

  setJob: (jobId: string, job: ParsedJob) => void;
  setClaims: (claims: ClaimedSkill[]) => void;
  setGithubEvidence: (evidence: GithubAnalyzeResponse | null) => void;
  setCurrentChallenge: (challenge: Challenge) => void;
  setEvaluation: (evaluation: SubmissionEvaluationResponse) => void;
  setReadiness: (readiness: ReadinessResponse) => void;
  reset: () => void;
}

const initialState = {
  jobId: null,
  job: null,
  claims: [],
  githubEvidence: null,
  currentChallenge: null,
  evaluation: null,
  readiness: null,
} satisfies Partial<SessionState>;

export const useSessionStore = create<SessionState>((set) => ({
  ...initialState,
  setJob: (jobId, job) => set({ jobId, job }),
  setClaims: (claims) => set({ claims }),
  setGithubEvidence: (githubEvidence) => set({ githubEvidence }),
  setCurrentChallenge: (currentChallenge) => set({ currentChallenge }),
  setEvaluation: (evaluation) => set({ evaluation }),
  setReadiness: (readiness) => set({ readiness }),
  reset: () => set(initialState),
}));
