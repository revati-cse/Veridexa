import type {
  ChallengeGenerateRequest,
  ChallengeGenerateResponse,
  ChallengeMutateRequest,
  ChallengeMutateResponse,
  ClaimsRequest,
  EvidenceComputeRequest,
  EvidenceListResponse,
  GithubAnalyzeRequest,
  GithubAnalyzeResponse,
  JobParseRequest,
  JobParseResponse,
  ReadinessComputeRequest,
  ReadinessResponse,
  SkillTaxonomyItem,
  SubmissionCreate,
  SubmissionEvaluationResponse,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<TResponse>(path: string, init?: RequestInit): Promise<TResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(0, "Could not reach the Veridexa backend. Check your connection and try again.");
  }

  if (!res.ok) {
    const fallback = `Request to ${path} failed with status ${res.status}`;
    const bodyText = await res.text().catch(() => "");
    let message = bodyText || fallback;
    try {
      const parsed = JSON.parse(bodyText);
      if (typeof parsed?.detail === "string") message = parsed.detail;
    } catch {
      // body wasn't JSON (or had no .detail) — keep the raw text/fallback above
    }
    throw new ApiError(res.status, message);
  }

  return (await res.json()) as TResponse;
}

export const api = {
  parseJob: (body: JobParseRequest) =>
    request<JobParseResponse>("/jobs/parse", { method: "POST", body: JSON.stringify(body) }),

  getTaxonomy: () => request<SkillTaxonomyItem[]>("/skills/taxonomy"),

  saveClaims: (body: ClaimsRequest) =>
    request<{ status: string; claims_saved: number }>("/candidates/claims", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  analyzeGithub: (body: GithubAnalyzeRequest) =>
    request<GithubAnalyzeResponse>("/github/analyze", { method: "POST", body: JSON.stringify(body) }),

  generateChallenge: (body: ChallengeGenerateRequest) =>
    request<ChallengeGenerateResponse>("/challenges/generate", { method: "POST", body: JSON.stringify(body) }),

  mutateChallenge: (body: ChallengeMutateRequest) =>
    request<ChallengeMutateResponse>("/challenges/mutate", { method: "POST", body: JSON.stringify(body) }),

  submitSolution: (body: SubmissionCreate) =>
    request<SubmissionEvaluationResponse>("/submissions", { method: "POST", body: JSON.stringify(body) }),

  computeReadiness: (body: ReadinessComputeRequest) =>
    request<ReadinessResponse>("/readiness/compute", { method: "POST", body: JSON.stringify(body) }),

  computeEvidence: (body: EvidenceComputeRequest) =>
    request<EvidenceListResponse>("/evidence/compute", { method: "POST", body: JSON.stringify(body) }),
};
