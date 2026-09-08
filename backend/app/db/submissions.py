"""Persistence for `submissions` / `evaluations`.

/submissions (BLUEPRINT.md's "no DB yet" contract fix) receives the full
Challenge object from the frontend rather than looking it up by id, so
there's no guarantee it was already persisted (the DB could have been down
when it was generated, or generated in an earlier session). save_challenge
is called here too — upserting on conflict — so the FK is always satisfied
regardless of that history.
"""

from uuid import UUID

import asyncpg

from app.db.challenges import _row_to_challenge, save_challenge
from app.db.pool import acquire, is_available
from app.db.users import ensure_user
from app.schemas.challenge import Challenge
from app.schemas.evaluation import SkillGapItem, SqlExecutionResult, SubmissionEvaluationResponse, SubmissionRecord


async def save_submission_and_evaluation(
    challenge: Challenge,
    user_id: UUID,
    code: str,
    explanation: str,
    response: SubmissionEvaluationResponse,
) -> None:
    if not is_available():
        return

    await ensure_user(user_id)
    await save_challenge(challenge, user_id)

    async with acquire() as conn, conn.transaction():
        await conn.execute(
            """INSERT INTO submissions (id, challenge_id, user_id, code, explanation)
               VALUES ($1, $2, $3, $4, $5) ON CONFLICT (id) DO NOTHING""",
            response.submission_id, challenge.id, user_id, code, explanation,
        )
        await conn.execute(
            """INSERT INTO evaluations (
                   id, submission_id, rubric_scores, overall_score, strengths,
                   weaknesses, skill_gaps, sql_execution_result
               ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
               ON CONFLICT (id) DO NOTHING""",
            response.evaluation_id,
            response.submission_id,
            response.rubric_scores,
            response.overall_score,
            response.strengths,
            response.weaknesses,
            [gap.model_dump() for gap in response.skill_gaps],
            response.sql_execution_result.model_dump() if response.sql_execution_result else None,
        )


def _row_to_submission_record(row: asyncpg.Record) -> SubmissionRecord:
    sql_result = row["sql_execution_result"]
    return SubmissionRecord(
        challenge=_row_to_challenge(row),
        evaluation=SubmissionEvaluationResponse(
            submission_id=row["submission_id"],
            evaluation_id=row["evaluation_id"],
            rubric_scores=row["rubric_scores"],
            overall_score=row["overall_score"],
            strengths=list(row["strengths"]),
            weaknesses=list(row["weaknesses"]),
            evidence=[],  # evaluations doesn't persist this column — see evidence.py's separate table
            skill_gaps=[SkillGapItem(**gap) for gap in row["skill_gaps"]],
            sql_execution_result=SqlExecutionResult(**sql_result) if sql_result else None,
            demo_fallback=False,  # historical rows don't record which path produced them
            evaluated_at=row["evaluated_at"],
        ),
    )


async def get_submission_history_for_job(job_id: UUID, user_id: UUID) -> list[SubmissionRecord]:
    """One candidate's full challenge+evaluation history for a job, oldest
    first — the same shape readiness_engine.compute_readiness expects for
    `submission_history`, reconstructed from persisted rows instead of the
    frontend's session store. Backs the recruiter dashboard (Section B, P3):
    there's no other way to see a candidate's performance across a job
    without a database, since the live compute path only ever knows about
    one candidate's current session.

    `evidence` is always empty on the reconstructed evaluations (the
    `evaluations` table doesn't persist per-observation evidence rows — see
    the module docstring above) — harmless here since neither
    readiness_engine nor skill_gap_engine reads that field, only
    evidence_engine.py does, and this function isn't used for that.
    Only the most recent submission per challenge is used, in case a
    challenge was ever submitted more than once."""
    if not is_available():
        return []
    async with acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT c.*, s.id AS submission_id, e.id AS evaluation_id,
                   e.rubric_scores, e.overall_score, e.strengths, e.weaknesses,
                   e.skill_gaps, e.sql_execution_result, e.created_at AS evaluated_at
            FROM challenges c
            JOIN LATERAL (
                SELECT * FROM submissions sub
                WHERE sub.challenge_id = c.id
                ORDER BY sub.submitted_at DESC LIMIT 1
            ) s ON true
            JOIN evaluations e ON e.submission_id = s.id
            WHERE c.job_id = $1 AND c.user_id = $2
            ORDER BY c.created_at ASC
            """,
            job_id, user_id,
        )
    return [_row_to_submission_record(row) for row in rows]
