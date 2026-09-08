from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.evaluation import SubmissionRecord
from app.schemas.github import GithubAnalyzeResponse
from app.schemas.job import JobRequiredSkill

FreshnessLabel = Literal["fresh", "aging", "stale", "not_assessed"]


class SkillFreshnessItem(BaseModel):
    """One row of freshness_engine.py's output — how long ago the most
    recent evidence for this skill was produced, not how strong it was
    (that's readiness_engine's job)."""

    skill: str
    last_evidence_at: datetime | None = None
    days_since_last_evidence: int | None = None
    freshness: FreshnessLabel


class FreshnessComputeRequest(BaseModel):
    """No DB persistence required — computed directly from the session
    state the frontend already holds, same "no DB yet" contract as
    readiness/evidence (see CLAUDE.md)."""

    user_id: UUID
    required_skills: list[JobRequiredSkill]
    github_evidence: GithubAnalyzeResponse | None = None
    submission_history: list[SubmissionRecord] = []


class FreshnessResponse(BaseModel):
    user_id: UUID
    skills: list[SkillFreshnessItem]
