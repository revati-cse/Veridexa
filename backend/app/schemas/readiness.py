from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import Importance
from app.schemas.evaluation import SkillGapItem


class SkillScoreBreakdown(BaseModel):
    """One row of the readiness_engine.py formula (Section N), rendered
    directly in the 'why is this candidate X% ready' explainer — the UI
    shows this arithmetic rather than hiding it behind a single number."""

    skill: str
    importance: Importance
    importance_weight: int  # high=3, medium=2, low=1
    score: float = Field(ge=0, le=100)
    weighted_contribution: float


class ReadinessResponse(BaseModel):
    user_id: UUID
    job_id: UUID
    job_title: str
    readiness_score: float = Field(ge=0, le=100)
    skill_breakdown: list[SkillScoreBreakdown]
    strengths: list[str]
    weaknesses: list[str]
    skill_gaps: list[SkillGapItem]
