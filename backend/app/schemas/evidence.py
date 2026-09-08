from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import EvidenceSourceType


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


class EvidenceListResponse(BaseModel):
    user_id: UUID
    skills: list[SkillEvidenceGroup]
