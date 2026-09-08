"""Persistence for the `users` table — just enough to satisfy the FK every
other table references. No real auth for the hackathon (Section T); a
candidate id is generated client-side and used as the primary key directly.
"""

from uuid import UUID

from app.db.pool import acquire, is_available


async def ensure_user(user_id: UUID) -> None:
    """Upserts a bare user row so user_id can be safely used as a foreign
    key by jobs/challenges/submissions/evidence/repositories. No-op if no
    database is configured."""
    if not is_available():
        return
    async with acquire() as conn:
        await conn.execute("INSERT INTO users (id) VALUES ($1) ON CONFLICT (id) DO NOTHING", user_id)
