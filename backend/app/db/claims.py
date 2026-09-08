"""Persistence for `candidate_claims` — see supabase/migrations/003_candidate_claims.sql.

A claim is never evidence (Section 2/L) — this table exists purely so
readiness_engine's claim-alignment bonus has something real to read per
candidate, instead of every caller passing claims=[] because nothing was
ever persisted. Matches the same best-effort, no-op-without-a-DB contract
as every other module in this package.
"""

from uuid import UUID

from app.db.pool import acquire, is_available
from app.db.skills import get_skill_id
from app.db.users import ensure_user
from app.schemas.skill import ClaimedSkill


async def save_claims(user_id: UUID, claims: list[ClaimedSkill]) -> None:
    if not is_available() or not claims:
        return
    await ensure_user(user_id)
    async with acquire() as conn, conn.transaction():
        for claim in claims:
            skill_id = await get_skill_id(conn, claim.skill)
            if skill_id is None:
                continue  # not in the taxonomy — nothing to link the claim to
            await conn.execute(
                """INSERT INTO candidate_claims (user_id, skill_id, level)
                   VALUES ($1, $2, $3)
                   ON CONFLICT (user_id, skill_id) DO UPDATE SET level = EXCLUDED.level, claimed_at = now()""",
                user_id, skill_id, claim.level,
            )


async def get_claims(user_id: UUID) -> list[ClaimedSkill]:
    """Returns [] both when no database is configured and when the
    candidate simply hasn't claimed anything yet — callers already treat an
    empty claims list as "no claim-alignment bonus for any skill" either
    way, so there's no "not assessed" distinction to preserve here (unlike
    skills.get_taxonomy's None vs [] split)."""
    if not is_available():
        return []
    async with acquire() as conn:
        rows = await conn.fetch(
            """SELECT s.name, cc.level FROM candidate_claims cc
               JOIN skills s ON s.id = cc.skill_id
               WHERE cc.user_id = $1""",
            user_id,
        )
    return [ClaimedSkill(skill=row["name"], level=row["level"]) for row in rows]
