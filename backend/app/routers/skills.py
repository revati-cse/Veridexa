from uuid import uuid4

from fastapi import APIRouter

from app.db.skills import get_taxonomy as get_db_taxonomy
from app.schemas import SkillTaxonomyItem
from app.services.skill_engine import get_taxonomy

router = APIRouter(prefix="/skills", tags=["skills"])

# uuid4() per item is regenerated on every process start since this is the
# no-DB fallback — fine for a hackathon (names are the stable identity the
# frontend keys off), but means these ids aren't durable across restarts.
# Used whenever no database is configured, or the DB read fails.
_FALLBACK_TAXONOMY_RESPONSE = [
    SkillTaxonomyItem(id=uuid4(), name=skill.name, category=skill.category) for skill in get_taxonomy()
]


@router.get("/taxonomy", response_model=list[SkillTaxonomyItem])
async def get_taxonomy_endpoint() -> list[SkillTaxonomyItem]:
    db_taxonomy = await get_db_taxonomy()
    if db_taxonomy:
        return db_taxonomy
    return _FALLBACK_TAXONOMY_RESPONSE
