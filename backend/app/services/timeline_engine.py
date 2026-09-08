"""timeline_engine service — BLUEPRINT.md Section B (P3, optional).

Pure function, no AI call, no DB read required: reshapes submission_history
into a per-skill chronological score history — the "Statistics 38.8% ->
70.8%" narrative (docs/demo_script.md) as data, not just a before/after
pair. readiness_engine.py already collapses this same history down to
"latest wins" for the current score; this exposes every point along the
way instead of only the last one, for a timeline view.

submission_history is passed in oldest-first (BLUEPRINT.md Section D — the
frontend appends to it as the candidate completes challenges), so entries
are built in that same order without needing to sort by timestamp.
"""

from uuid import UUID

from app.schemas.evaluation import SubmissionRecord
from app.schemas.timeline import SkillTimeline, SkillTimelineEntry, TimelineResponse
from app.services.skill_engine import normalize_skill


def compute_timeline(user_id: UUID, submission_history: list[SubmissionRecord]) -> TimelineResponse:
    # Keyed by lowercase for matching, but the display name (correctly cased
    # for a taxonomy skill, as-typed otherwise) is only ever computed once
    # per skill and stored alongside — re-deriving it from the lowercased
    # key would silently lose casing for a skill outside the taxonomy,
    # since normalize_skill only trims-and-returns an unrecognized name
    # rather than restoring its original case.
    display_names: dict[str, str] = {}
    entries_by_skill: dict[str, list[SkillTimelineEntry]] = {}
    order: list[str] = []

    for record in submission_history:
        entry = SkillTimelineEntry(
            timestamp=record.evaluation.evaluated_at,
            score=record.evaluation.overall_score,
            challenge_title=record.challenge.title,
            mutation_reason=record.challenge.mutation_reason,
        )
        for skill in record.challenge.required_skills:
            canonical = normalize_skill(skill)
            key = canonical.lower()
            if key not in entries_by_skill:
                entries_by_skill[key] = []
                display_names[key] = canonical
                order.append(key)
            entries_by_skill[key].append(entry)

    skills = [
        SkillTimeline(skill=display_names[key], entries=entries_by_skill[key])
        for key in order
    ]
    return TimelineResponse(user_id=user_id, skills=skills)
