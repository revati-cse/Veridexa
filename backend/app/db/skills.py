"""Persistence for the `skills` table. skill_engine.py remains the single
source of truth for the canonical taxonomy content (Section 2) — this
module only reads/writes rows that mirror it, and resolves skill names to
their DB id as the FK target for job_skills/evidence/repository_evidence.
"""

from uuid import UUID

import asyncpg

from app.db.pool import acquire, is_available
from app.schemas.skill import SkillTaxonomyItem


async def get_taxonomy() -> list[SkillTaxonomyItem] | None:
    """Returns None (not an empty list) if no database is configured, so
    routers/skills.py can distinguish "no DB" from "DB has no skills yet"
    and fall back to the in-process taxonomy list accordingly."""
    if not is_available():
        return None
    async with acquire() as conn:
        rows = await conn.fetch("SELECT id, name, category FROM skills ORDER BY category, name")
    return [SkillTaxonomyItem(id=r["id"], name=r["name"], category=r["category"]) for r in rows]


async def get_skill_id(conn: asyncpg.Connection, name: str) -> UUID | None:
    """Resolves a canonical skill name (already normalized by
    skill_engine.normalize_skill) to its DB id. Returns None for a skill
    not in the taxonomy — callers should skip linking rather than fail the
    whole write, since an unrecognized skill is still shown to the user
    (Section 2), just not taxonomy-backed."""
    row = await conn.fetchrow("SELECT id FROM skills WHERE name = $1", name)
    return row["id"] if row else None
