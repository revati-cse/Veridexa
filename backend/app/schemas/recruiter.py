from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.evaluation import SkillGapItem
from app.schemas.readiness import SkillScoreBreakdown


class CandidateSummary(BaseModel):
    """One row of the recruiter dashboard — readiness_score is computed by
    the exact same readiness_engine.compute_readiness formula the candidate
    sees on their own dashboard, from persisted challenge/evaluation history
    (never a separately-derived recruiter-side number). skill_breakdown is
    the same per-skill rows compute_readiness already produces — carried
    here so the frontend can build a candidate-comparison view straight
    from this one payload, with no second endpoint or recomputation."""

    user_id: UUID
    readiness_score: float = Field(ge=0, le=100)
    challenges_completed: int
    strengths: list[str]
    weaknesses: list[str]
    skill_gaps: list[SkillGapItem]
    skill_breakdown: list[SkillScoreBreakdown]


class RecruiterDashboardResponse(BaseModel):
    """DB-backed — unlike every other compute-from-session-state endpoint,
    a recruiter needs to see candidates across sessions, so this is only
    ever populated when DATABASE_URL is configured. `db_available: false`
    (with an empty `candidates` list) tells the frontend why the dashboard
    is empty, rather than it looking like "no candidates applied yet"."""

    job_id: UUID
    job_title: str
    db_available: bool
    candidates: list[CandidateSummary]
