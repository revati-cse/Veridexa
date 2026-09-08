"""Persistence for `repositories` / `repository_evidence`."""

from uuid import UUID

from app.db.pool import acquire, is_available
from app.db.skills import get_skill_id
from app.db.users import ensure_user
from app.schemas.github import LanguageDetected, SkillEvidenceItem


async def save_repository_analysis(
    repository_id: UUID,
    user_id: UUID,
    url: str,
    languages_detected: list[LanguageDetected],
    skills: list[SkillEvidenceItem],
) -> None:
    if not is_available():
        return

    await ensure_user(user_id)

    languages_summary = {item.language: item.confidence for item in languages_detected}

    async with acquire() as conn, conn.transaction():
        await conn.execute(
            """INSERT INTO repositories (id, user_id, url, languages_summary, analyzed_at)
               VALUES ($1, $2, $3, $4, now()) ON CONFLICT (id) DO NOTHING""",
            repository_id, user_id, url, languages_summary,
        )
        for skill in skills:
            if skill.evidence_strength == "none":
                continue  # repository_evidence's check constraint only allows weak/moderate/strong —
                # "no evidence" isn't a row to store, consistent with evidence_engine.py
                # skipping skills with zero observations.
            skill_id = await get_skill_id(conn, skill.skill)
            if skill_id is None:
                continue  # not in the taxonomy — nothing to link repository_evidence to
            await conn.execute(
                """INSERT INTO repository_evidence
                       (repository_id, skill_id, evidence_strength, confidence, observations)
                   VALUES ($1, $2, $3, $4, $5)""",
                repository_id, skill_id, skill.evidence_strength, skill.confidence, skill.observations,
            )
