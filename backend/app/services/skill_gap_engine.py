"""skill_gap_engine service — BLUEPRINT.md Feature 7 / Section O.

Pure function, no AI call: compares each required skill's readiness-computed
score against a threshold and flags the ones that fall short. Missing
concepts are reused directly from whatever evaluation most recently
produced a SkillGapItem for that skill — never re-derived with a fresh
Claude call ("reuse it rather than asking Claude twice", Section O).
"""

from app.schemas.evaluation import SkillGapItem, SubmissionRecord
from app.schemas.readiness import SkillScoreBreakdown

_IMPORTANCE_RANK = {"high": 3, "medium": 2, "low": 1}

# Deliberately more sensitive than readiness_engine's "weaknesses" cutoff
# (60) — a skill can be good enough to avoid the "weakness" label on the
# dashboard summary while still being worth a dedicated gap card and a
# targeted next challenge (e.g. the Section 26 demo's Statistics at 61%).
GAP_SCORE_THRESHOLD = 70.0


def _missing_concepts_by_skill(submission_history: list[SubmissionRecord]) -> dict[str, list[str]]:
    """Most recent evaluation's SkillGapItem per skill (normalized lowercase
    key) — later submissions overwrite earlier ones, same "latest wins"
    convention as readiness_engine's challenge scores."""
    concepts: dict[str, list[str]] = {}
    for record in submission_history:
        for gap in record.evaluation.skill_gaps:
            concepts[gap.skill.lower()] = gap.missing_concepts
    return concepts


def compute_skill_gaps(
    skill_breakdown: list[SkillScoreBreakdown],
    submission_history: list[SubmissionRecord],
) -> list[SkillGapItem]:
    concepts_by_skill = _missing_concepts_by_skill(submission_history)

    gap_rows = [row for row in skill_breakdown if row.score < GAP_SCORE_THRESHOLD]
    # Highest importance first, then lowest score first within the same importance.
    gap_rows.sort(key=lambda row: (-_IMPORTANCE_RANK[row.importance], row.score))

    return [
        SkillGapItem(skill=row.skill, missing_concepts=concepts_by_skill.get(row.skill.lower(), []))
        for row in gap_rows
    ]
