from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.github import ClaimVsEvidenceItem, SkillEvidenceItem
from app.schemas.skill import ClaimedSkill


class ProjectDescriptionAnalyzeRequest(BaseModel):
    """The evidence path for a candidate with a real project but no
    repository link — a free-text description analyzed the same way
    github_analyzer.py analyzes repository files (see
    project_description_analyzer.py)."""

    user_id: UUID
    description: str = Field(min_length=20, max_length=4000)
    claimed_skills: list[ClaimedSkill] = []
    required_skills: list[str] = []


class ProjectDescriptionAnalyzeResponse(BaseModel):
    source_id: UUID
    skills: list[SkillEvidenceItem]
    claims_vs_evidence: list[ClaimVsEvidenceItem]
    demo_fallback: bool = False
    # Set server-side when this response is built (never client-supplied) —
    # round-trips unchanged once passed back into a later request (e.g. as
    # `project_description_evidence` on /readiness/compute).
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
