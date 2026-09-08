from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import EvidenceSourceType
from app.schemas.evaluation import SubmissionRecord
from app.schemas.github import GithubAnalyzeResponse
from app.schemas.project import ProjectDescriptionAnalyzeResponse


class EvidenceItem(BaseModel):
    id: UUID
    skill: str
    source_type: EvidenceSourceType
    source_reference: str | None = None
    observation: str
    confidence: float = Field(ge=0, le=1)
    created_at: datetime


class SkillEvidenceGroup(BaseModel):
    """Every skill % shown in the UI must trace back to this list — never
    render a confidence number with an empty `evidence` list."""

    skill: str
    evidence: list[EvidenceItem]


class EvidenceComputeRequest(BaseModel):
    """No DB persistence yet, so evidence is computed directly from the
    session state the frontend already holds, rather than looked up by
    user_id. Deliberately carries no `claims` field — a claim is not
    evidence (BLUEPRINT.md Section 2), so it can't feed into this endpoint
    even by accident; claims only ever factor into readiness_engine's
    claim-alignment bonus, never into what's shown as "evidence"."""

    user_id: UUID
    github_evidence: GithubAnalyzeResponse | None = None
    project_description_evidence: ProjectDescriptionAnalyzeResponse | None = None
    submission_history: list[SubmissionRecord] = []


class EvidenceListResponse(BaseModel):
    user_id: UUID
    skills: list[SkillEvidenceGroup]
