from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.evaluation import SubmissionRecord


class SkillTimelineEntry(BaseModel):
    """One attempt's contribution to a skill's score history — the same
    overall_score readiness_engine already weighs in, just kept per-attempt
    instead of collapsed to "latest wins"."""

    timestamp: datetime
    score: float = Field(ge=0, le=100)
    challenge_title: str
    # Set only when this attempt's challenge was a mutation targeting a
    # prior weak point — the UI's "why did this jump" caption.
    mutation_reason: str | None = None


class SkillTimeline(BaseModel):
    skill: str
    entries: list[SkillTimelineEntry]  # chronological, oldest first


class TimelineComputeRequest(BaseModel):
    """No DB persistence required — computed directly from the session
    state the frontend already holds, same "no DB yet" contract as
    readiness/evidence/freshness (see CLAUDE.md)."""

    user_id: UUID
    submission_history: list[SubmissionRecord] = []


class TimelineResponse(BaseModel):
    user_id: UUID
    skills: list[SkillTimeline]
