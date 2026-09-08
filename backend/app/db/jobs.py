"""Persistence for `jobs` / `job_skills`.

Known limitation: the `jobs` table (Section F) only carries title +
raw_description — soft_skills/tools/experience_years from ParsedJob have no
column to land in. Expanding the schema is a follow-up, not done here;
get_job() returns those fields empty rather than guessing at a shape.
"""

from uuid import UUID

from app.db.pool import acquire, is_available
from app.db.skills import get_skill_id
from app.schemas.job import JobRequiredSkill, ParsedJob


async def save_job(job_id: UUID, raw_description: str, job: ParsedJob) -> None:
    if not is_available():
        return
    async with acquire() as conn, conn.transaction():
        await conn.execute(
            "INSERT INTO jobs (id, title, raw_description) VALUES ($1, $2, $3) ON CONFLICT (id) DO NOTHING",
            job_id, job.title, raw_description,
        )
        for requirement in job.required_skills:
            skill_id = await get_skill_id(conn, requirement.skill)
            if skill_id is None:
                continue  # not in the taxonomy — nothing to link job_skills to
            await conn.execute(
                """INSERT INTO job_skills (job_id, skill_id, importance, required)
                   VALUES ($1, $2, $3, $4)
                   ON CONFLICT (job_id, skill_id)
                   DO UPDATE SET importance = EXCLUDED.importance, required = EXCLUDED.required""",
                job_id, skill_id, requirement.importance, requirement.required,
            )


async def get_job(job_id: UUID) -> ParsedJob | None:
    if not is_available():
        return None
    async with acquire() as conn:
        job_row = await conn.fetchrow("SELECT title FROM jobs WHERE id = $1", job_id)
        if job_row is None:
            return None
        skill_rows = await conn.fetch(
            """SELECT s.name, js.importance, js.required
               FROM job_skills js JOIN skills s ON s.id = js.skill_id
               WHERE js.job_id = $1
               ORDER BY js.importance, s.name""",
            job_id,
        )
    return ParsedJob(
        title=job_row["title"],
        required_skills=[
            JobRequiredSkill(skill=r["name"], importance=r["importance"], required=r["required"])
            for r in skill_rows
        ],
        soft_skills=[],
        tools=[],
        experience_years=None,
    )
