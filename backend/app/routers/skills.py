from uuid import uuid4

from fastapi import APIRouter

from app.schemas import SkillTaxonomyItem
from app.services.skill_engine import get_taxonomy

router = APIRouter(prefix="/skills", tags=["skills"])

# uuid4() per item is regenerated on every process start since there's no DB
# yet — fine for a hackathon (names are the stable identity the frontend
# keys off), but means these ids aren't durable across restarts.
_TAXONOMY_RESPONSE = [
    SkillTaxonomyItem(id=uuid4(), name=skill.name, category=skill.category) for skill in get_taxonomy()
]


@router.get("/taxonomy", response_model=list[SkillTaxonomyItem])
async def get_taxonomy_endpoint() -> list[SkillTaxonomyItem]:
    return _TAXONOMY_RESPONSE
