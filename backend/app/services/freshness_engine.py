"""freshness_engine service — BLUEPRINT.md Section B (P2, optional).

Pure function, no AI call, no DB read required: flags whether the evidence
behind each required skill is recent or stale, using the same two evidence
sources evidence_engine.py already knows about (GitHub analysis and
challenge submissions) — `resume`/`project` evidence types exist in the
schema but nothing currently produces them, so they're not inputs here.

Deliberately informational-only. "How confident are we" (readiness_engine's
score) and "how current is that confidence" (this) are different questions,
and blending them would make the numbers verified in docs/demo_script.md
non-reproducible for no product benefit — a hackathon demo doesn't need
evidence to decay mid-rehearsal. If a real decay-into-score feature is
wanted later, it belongs in readiness_engine's own weighting, as a
deliberate, separately-verified change — not smuggled in here.
"""

from datetime import datetime, timezone
from uuid import UUID

from app.schemas.evaluation import SubmissionRecord
from app.schemas.freshness import FreshnessLabel, FreshnessResponse, SkillFreshnessItem
from app.schemas.github import GithubAnalyzeResponse
from app.schemas.job import JobRequiredSkill
from app.services.skill_engine import normalize_skill

FRESH_MAX_DAYS = 30
AGING_MAX_DAYS = 180


def _bucket(days: int | None) -> FreshnessLabel:
    if days is None:
        return "not_assessed"
    if days <= FRESH_MAX_DAYS:
        return "fresh"
    if days <= AGING_MAX_DAYS:
        return "aging"
    return "stale"


def _latest_evidence_timestamps(
    github_evidence: GithubAnalyzeResponse | None,
    submission_history: list[SubmissionRecord],
) -> dict[str, datetime]:
    """Most recent evidence timestamp per normalized skill key, across both
    sources — "latest wins" per skill, same convention readiness_engine and
    skill_gap_engine already use for combining multiple evidence rows."""
    latest: dict[str, datetime] = {}

    def _record(skill: str, timestamp: datetime) -> None:
        key = normalize_skill(skill).lower()
        if key not in latest or timestamp > latest[key]:
            latest[key] = timestamp

    if github_evidence is not None:
        for skill_evidence in github_evidence.skills:
            if skill_evidence.evidence_strength == "none":
                continue  # no evidence was actually produced for this skill
            _record(skill_evidence.skill, github_evidence.analyzed_at)

    for record in submission_history:
        for skill in record.challenge.required_skills:
            _record(skill, record.evaluation.evaluated_at)

    return latest


def compute_freshness(
    user_id: UUID,
    required_skills: list[JobRequiredSkill],
    github_evidence: GithubAnalyzeResponse | None,
    submission_history: list[SubmissionRecord],
    now: datetime | None = None,
) -> FreshnessResponse:
    now = now or datetime.now(timezone.utc)
    latest_by_skill = _latest_evidence_timestamps(github_evidence, submission_history)

    items: list[SkillFreshnessItem] = []
    for requirement in required_skills:
        skill = normalize_skill(requirement.skill)
        timestamp = latest_by_skill.get(skill.lower())
        days = (now - timestamp).days if timestamp is not None else None
        items.append(
            SkillFreshnessItem(
                skill=skill,
                last_evidence_at=timestamp,
                days_since_last_evidence=days,
                freshness=_bucket(days),
            )
        )

    return FreshnessResponse(user_id=user_id, skills=items)
