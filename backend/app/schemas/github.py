from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ClaimLevel, EvidenceStrength


class GithubAnalyzeRequest(BaseModel):
    user_id: UUID
    repository_url: str = Field(pattern=r"^https://github\.com/[\w.-]+/[\w.-]+/?$")
    claimed_skills: list[str] = []
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


class GithubAnalyzeResponse(BaseModel):
    repository_id: UUID
    repository: str
    languages_detected: list[LanguageDetected]
    skills: list[SkillEvidenceItem]
    claims_vs_evidence: list[ClaimVsEvidenceItem]
    demo_fallback: bool = False
