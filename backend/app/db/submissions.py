"""Persistence for `submissions` / `evaluations`.

/submissions (BLUEPRINT.md's "no DB yet" contract fix) receives the full
Challenge object from the frontend rather than looking it up by id, so
there's no guarantee it was already persisted (the DB could have been down
when it was generated, or generated in an earlier session). save_challenge
is called here too — upserting on conflict — so the FK is always satisfied
regardless of that history.
"""

from uuid import UUID

from app.db.challenges import save_challenge
from app.db.pool import acquire, is_available
from app.db.users import ensure_user
from app.schemas.challenge import Challenge
from app.schemas.evaluation import SubmissionEvaluationResponse


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
