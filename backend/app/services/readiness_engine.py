"""readiness_engine service — BLUEPRINT.md Feature 6 / Section N.

Pure backend arithmetic, no AI call: the LLM is never involved in computing
a skill score or the final readiness percentage. Each skill's score blends
whichever of (latest challenge evidence, GitHub evidence, claim alignment)
is actually available, normalizing the weights over just the components
present — so a skill with only strong GitHub evidence isn't unfairly capped
by the 60% weight reserved for challenge evidence it hasn't earned yet.
"""

from uuid import UUID

from app.schemas.evaluation import SubmissionRecord
from app.schemas.github import GithubAnalyzeResponse
from app.schemas.job import JobRequiredSkill
from app.schemas.readiness import ReadinessResponse, SkillScoreBreakdown
from app.schemas.skill import ClaimedSkill
from app.services.skill_engine import normalize_skill

_IMPORTANCE_WEIGHT = {"high": 3, "medium": 2, "low": 1}

_GITHUB_EVIDENCE_SCORE = {"strong": 90.0, "moderate": 65.0, "weak": 35.0, "none": 0.0}

_CHALLENGE_WEIGHT = 0.6
_GITHUB_WEIGHT = 0.3
_CLAIM_WEIGHT = 0.1

_STRENGTH_THRESHOLD = 80.0
_WEAKNESS_THRESHOLD = 60.0
# A claim counts as "corroborated" (full alignment credit) only once some
# other evidence source backs it at least moderately — an uncorroborated
# claim still earns a small credit (it's on record, not contradicted), just
# far short of what actual evidence would give it.
_CORROBORATION_THRESHOLD = 60.0
_CORROBORATED_CLAIM_BONUS = 100.0
_UNCORROBORATED_CLAIM_BONUS = 50.0


def _latest_challenge_scores(submission_history: list[SubmissionRecord]) -> dict[str, float]:
    """Each submission's overall_score applies to every skill its challenge
    targeted. `submission_history` is oldest-first (how the frontend appends
    to it), so iterating in order and overwriting naturally keeps only the
    most recent score per skill — exactly the "improved after mutation"
    behavior the product is built around."""
    scores: dict[str, float] = {}
    for record in submission_history:
        for skill in record.challenge.required_skills:
            scores[normalize_skill(skill).lower()] = record.evaluation.overall_score
    return scores


def _github_scores(github_evidence: GithubAnalyzeResponse | None) -> dict[str, float]:
    if github_evidence is None:
        return {}
    return {
        normalize_skill(item.skill).lower(): _GITHUB_EVIDENCE_SCORE[item.evidence_strength]
        for item in github_evidence.skills
    }


def _claim_alignment_bonus(has_claim: bool, corroborating_score: float | None) -> float | None:
    """None means "no component" (skill was never claimed at all) — distinct
    from a low bonus, and excluded entirely from the weighted average below
    rather than treated as a 0."""
    if not has_claim:
        return None
    if corroborating_score is not None and corroborating_score >= _CORROBORATION_THRESHOLD:
        return _CORROBORATED_CLAIM_BONUS
    return _UNCORROBORATED_CLAIM_BONUS


def _compute_skill_score(
    skill: str,
    claims_by_skill: dict[str, ClaimedSkill],
    challenge_scores: dict[str, float],
    github_scores: dict[str, float],
) -> float:
    key = skill.lower()
    challenge_score = challenge_scores.get(key)
    github_score = github_scores.get(key)
    corroborating = challenge_score if challenge_score is not None else github_score
    claim_bonus = _claim_alignment_bonus(key in claims_by_skill, corroborating)

    components: list[tuple[float, float]] = []
    if challenge_score is not None:
        components.append((challenge_score, _CHALLENGE_WEIGHT))
    if github_score is not None:
        components.append((github_score, _GITHUB_WEIGHT))
    if claim_bonus is not None:
        components.append((claim_bonus, _CLAIM_WEIGHT))

    if not components:
        return 0.0  # no evidence and no claim at all — "not yet assessed"

    total_weight = sum(weight for _, weight in components)
    return round(sum(value * weight for value, weight in components) / total_weight, 2)


def compute_readiness(
    user_id: UUID,
    job_id: UUID,
    job_title: str,
    required_skills: list[JobRequiredSkill],
    claims: list[ClaimedSkill],
    github_evidence: GithubAnalyzeResponse | None,
    submission_history: list[SubmissionRecord],
) -> ReadinessResponse:
    claims_by_skill = {normalize_skill(c.skill).lower(): c for c in claims}
    challenge_scores = _latest_challenge_scores(submission_history)
    github_scores = _github_scores(github_evidence)

    breakdown: list[SkillScoreBreakdown] = []
    for requirement in required_skills:
        skill = normalize_skill(requirement.skill)
        weight = _IMPORTANCE_WEIGHT[requirement.importance]
        score = _compute_skill_score(skill, claims_by_skill, challenge_scores, github_scores)
        breakdown.append(
            SkillScoreBreakdown(
                skill=skill,
                importance=requirement.importance,
                importance_weight=weight,
                score=score,
                weighted_contribution=round(score * weight, 2),
            )
        )

    numerator = sum(row.weighted_contribution for row in breakdown)
    denominator = sum(row.importance_weight for row in breakdown)
    readiness_score = round(numerator / denominator, 1) if denominator else 0.0

    strengths = [row.skill for row in breakdown if row.score >= _STRENGTH_THRESHOLD]
    weaknesses = [row.skill for row in breakdown if row.score < _WEAKNESS_THRESHOLD]

    # skill_gap_engine (next task) replaces this with proper sorting/dedup
    # per Section O; for now, surface the most recent submission's own
    # skill_gaps as-is rather than leaving the field empty when real data
    # already exists.
    skill_gaps = submission_history[-1].evaluation.skill_gaps if submission_history else []

    return ReadinessResponse(
        user_id=user_id,
        job_id=job_id,
        job_title=job_title,
        readiness_score=readiness_score,
        skill_breakdown=breakdown,
        strengths=strengths,
        weaknesses=weaknesses,
        skill_gaps=skill_gaps,
    )
