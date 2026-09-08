from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import Importance
from app.schemas.evaluation import SkillGapItem, SubmissionRecord
from app.schemas.github import GithubAnalyzeResponse
from app.schemas.job import JobRequiredSkill
from app.schemas.skill import ClaimedSkill


class SkillScoreBreakdown(BaseModel):
    """One row of the readiness_engine.py formula (Section N), rendered
    directly in the 'why is this candidate X% ready' explainer — the UI
    shows this arithmetic rather than hiding it behind a single number."""

    skill: str
    importance: Importance
    importance_weight: int  # high=3, medium=2, low=1
    score: float = Field(ge=0, le=100)
    weighted_contribution: float


class ReadinessComputeRequest(BaseModel):
    """No DB persistence yet, so readiness is computed directly from the
    session state the frontend already holds (it already has all of this —
    it's what drove the job/evidence/challenge screens) rather than looked
    up by job_id."""

    user_id: UUID
    job_id: UUID
    job_title: str
    required_skills: list[JobRequiredSkill]
    claims: list[ClaimedSkill] = []
    github_evidence: GithubAnalyzeResponse | None = None
    submission_history: list[SubmissionRecord] = []


class ReadinessResponse(BaseModel):
    user_id: UUID
    job_id: UUID
    job_title: str
    readiness_score: float = Field(ge=0, le=100)
    skill_breakdown: list[SkillScoreBreakdown]
    strengths: list[str]
    weaknesses: list[str]
    skill_gaps: list[SkillGapItem]
