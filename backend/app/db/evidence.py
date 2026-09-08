"""Persistence for the generic `evidence` table — the traceability backbone
behind every skill % shown in the UI (Section L). Rows are built by
evidence_engine.py at request time (no DB required for the live compute
path) and persisted here as a best-effort side-write from the router that
produced them, which is why challenge_id/repository_id are passed in
explicitly rather than carried on EvidenceItem itself.
"""

from uuid import UUID

from app.db.pool import acquire, is_available
from app.db.skills import get_skill_id
from app.db.users import ensure_user
from app.schemas.evidence import EvidenceItem


async def save_evidence_rows(
    rows: list[EvidenceItem],
    user_id: UUID,
    challenge_id: UUID | None = None,
    repository_id: UUID | None = None,
) -> None:
    if not is_available() or not rows:
        return

    await ensure_user(user_id)

    async with acquire() as conn, conn.transaction():
        for row in rows:
            skill_id = await get_skill_id(conn, row.skill)
            if skill_id is None:
                continue  # not in the taxonomy — nothing to link evidence to
            await conn.execute(
                """INSERT INTO evidence
                       (id, user_id, skill_id, source_type, source_reference,
                        challenge_id, repository_id, observation, confidence)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
                   ON CONFLICT (id) DO NOTHING""",
                row.id, user_id, skill_id, row.source_type, row.source_reference,
                challenge_id, repository_id, row.observation, row.confidence,
            )
