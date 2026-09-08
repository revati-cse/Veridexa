"""Persistence for `challenges` — including walking parent_challenge_id for
the challenge-history feature (BLUEPRINT.md Section 6 "Challenge history",
routers/challenges.py's /{id}/history endpoint).
"""

from uuid import UUID

import asyncpg

from app.db.pool import acquire, is_available
from app.db.users import ensure_user
from app.schemas.challenge import Challenge


def _row_to_challenge(row: asyncpg.Record) -> Challenge:
    return Challenge(
        id=row["id"],
        job_id=row["job_id"],
        parent_challenge_id=row["parent_challenge_id"],
        title=row["title"],
        role=row["role"],
        scenario=row["scenario"],
        instructions=row["instructions"],
        required_skills=list(row["required_skills"]),
        difficulty=row["difficulty"],
        dataset=row["dataset"],
        expected_output=row["expected_output"],
        evaluation_criteria=row["evaluation_criteria"],
        mutation_reason=row["mutation_reason"],
    )


async def _insert_challenge(conn: asyncpg.Connection, challenge: Challenge, user_id: UUID, job_id: UUID | None) -> None:
    await conn.execute(
        """INSERT INTO challenges (
               id, job_id, user_id, parent_challenge_id, title, role, scenario,
               instructions, required_skills, difficulty, dataset, expected_output,
               evaluation_criteria, mutation_reason
           ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
           ON CONFLICT (id) DO NOTHING""",
        challenge.id, job_id, user_id, challenge.parent_challenge_id,
        challenge.title, challenge.role, challenge.scenario, challenge.instructions,
        challenge.required_skills, challenge.difficulty, challenge.dataset,
        challenge.expected_output, challenge.evaluation_criteria, challenge.mutation_reason,
    )


async def save_challenge(challenge: Challenge, user_id: UUID) -> None:
    """job_id is passed by the frontend from session state with no guarantee
    it was ever persisted to `jobs` (the DB could have been down when
    /jobs/parse ran, or the challenge came from a demo/test flow that never
    called it) — a FK violation on job_id degrades to saving the challenge
    unlinked rather than losing the row entirely."""
    if not is_available():
        return
    await ensure_user(user_id)
    async with acquire() as conn:
        try:
            await _insert_challenge(conn, challenge, user_id, challenge.job_id)
        except asyncpg.ForeignKeyViolationError:
            await _insert_challenge(conn, challenge, user_id, None)


async def get_challenge(challenge_id: UUID) -> Challenge | None:
    if not is_available():
        return None
    async with acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM challenges WHERE id = $1", challenge_id)
    return _row_to_challenge(row) if row else None


async def get_challenge_chain(challenge_id: UUID) -> list[Challenge]:
    """Walks parent_challenge_id back to the root. Returns oldest-first (the
    original challenge through to the one requested) — [] if the challenge
    isn't found or no database is configured, never an error, since this
    backs a "nice to have" history view, not a critical path."""
    if not is_available():
        return []

    chain: list[Challenge] = []
    seen: set[UUID] = set()
    current_id: UUID | None = challenge_id

    async with acquire() as conn:
        while current_id is not None and current_id not in seen:
            seen.add(current_id)
            row = await conn.fetchrow("SELECT * FROM challenges WHERE id = $1", current_id)
            if row is None:
                break
            chain.append(_row_to_challenge(row))
            current_id = row["parent_challenge_id"]

    chain.reverse()
    return chain
