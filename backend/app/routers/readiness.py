from uuid import UUID

from fastapi import APIRouter

from app.schemas import ReadinessResponse, SkillGapItem
from app.schemas.readiness import SkillScoreBreakdown

router = APIRouter(prefix="/readiness", tags=["readiness"])

_IMPORTANCE_WEIGHT = {"high": 3, "medium": 2, "low": 1}

# STUB skill scores — real readiness_engine.py (Phase 10) blends
# challenge/github/claim evidence per BLUEPRINT.md Section N instead of a
# hardcoded dict. The weighting arithmetic below IS the real formula,
# applied to placeholder inputs, so this router already behaves correctly
# once real scores are substituted.
_STUB_SKILL_SCORES = {
    "SQL": 88.0,
    "Python": 82.0,
    "Statistics": 61.0,
    "Power BI": 73.0,
    "Problem Solving": 84.0,
}
_STUB_REQUIRED_SKILLS = [
    ("SQL", "high"), ("Python", "high"), ("Statistics", "medium"),
    ("Power BI", "medium"), ("Problem Solving", "high"),
]


def _compute_readiness(skill_scores: dict[str, float], required_skills: list[tuple[str, str]]):
    breakdown = []
    for skill, importance in required_skills:
        weight = _IMPORTANCE_WEIGHT[importance]
        score = skill_scores.get(skill, 0.0)
        breakdown.append(
            SkillScoreBreakdown(
                skill=skill, importance=importance, importance_weight=weight,
                score=score, weighted_contribution=round(score * weight, 2),
            )
        )
    numerator = sum(row.weighted_contribution for row in breakdown)
    denominator = sum(row.importance_weight for row in breakdown)
    readiness = round(numerator / denominator, 1) if denominator else 0.0
    return readiness, breakdown


@router.get("/{user_id}/{job_id}", response_model=ReadinessResponse)
async def get_readiness(user_id: UUID, job_id: UUID) -> ReadinessResponse:
    """STUB: skill_scores are hardcoded until evidence_engine.py /
    readiness_engine.py (Phase 9-10) compute them from real evidence rows.
    The Σ(score × importance_weight) / Σ(importance_weight) math itself is
    the real backend formula from BLUEPRINT.md Section N — never LLM-derived.
    """
    readiness_score, breakdown = _compute_readiness(_STUB_SKILL_SCORES, _STUB_REQUIRED_SKILLS)
    return ReadinessResponse(
        user_id=user_id,
        job_id=job_id,
        job_title="Data Analyst",
        readiness_score=readiness_score,
        skill_breakdown=breakdown,
        strengths=["SQL", "Problem Solving"],
        weaknesses=["Statistics"],
        skill_gaps=[
            SkillGapItem(skill="Statistics", missing_concepts=["Hypothesis testing", "Statistical significance", "A/B testing"]),
        ],
    )
