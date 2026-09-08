from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ClaimLevel, EvidenceStrength
from app.schemas.skill import ClaimedSkill


class GithubAnalyzeRequest(BaseModel):
    user_id: UUID
    repository_url: str = Field(pattern=r"^https://github\.com/[\w.-]+/[\w.-]+/?$")
    # Carries claim levels (not just names) — the claims_vs_evidence table
    # can't honestly report "claim: advanced" without this.
    claimed_skills: list[ClaimedSkill] = []
    required_skills: list[str] = []


class LanguageDetected(BaseModel):
    language: str
    confidence: float = Field(ge=0, le=1)


class SkillEvidenceItem(BaseModel):
    skill: str
    evidence_strength: EvidenceStrength
    confidence: float = Field(ge=0, le=1)
    observations: list[str] = []


class ClaimVsEvidenceItem(BaseModel):
    skill: str
    claim: ClaimLevel | None = None
    repository_evidence: EvidenceStrength
    assessment: str


class GithubAnalysisAIOutput(BaseModel):
    """What Claude actually returns from github_analysis_prompt.py — evidence
    per skill only. `languages_detected` is computed from the GitHub API's own
    byte-count stats (Section I step 3), and `claims_vs_evidence.assessment`
    is a deterministic backend rule (Section M) — neither is the LLM's call."""

    skills: list[SkillEvidenceItem]


class GithubAnalyzeResponse(BaseModel):
    repository_id: UUID
    repository: str
    languages_detected: list[LanguageDetected]
    skills: list[SkillEvidenceItem]
    claims_vs_evidence: list[ClaimVsEvidenceItem]
    demo_fallback: bool = False
