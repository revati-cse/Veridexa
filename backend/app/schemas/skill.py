from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ClaimLevel, SkillCategory


class SkillTaxonomyItem(BaseModel):
    """One row of the fixed 30-50 skill taxonomy, returned by GET /skills/taxonomy."""

    id: UUID
    name: str
    category: SkillCategory


class ClaimedSkill(BaseModel):
    skill: str
    level: ClaimLevel


class ClaimsRequest(BaseModel):
    user_id: UUID
    claims: list[ClaimedSkill]
