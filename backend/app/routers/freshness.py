from fastapi import APIRouter

from app.schemas.freshness import FreshnessComputeRequest, FreshnessResponse
from app.services.freshness_engine import compute_freshness

router = APIRouter(prefix="/freshness", tags=["freshness"])


@router.post("/compute", response_model=FreshnessResponse)
async def compute_freshness_endpoint(request: FreshnessComputeRequest) -> FreshnessResponse:
    """P2/optional per BLUEPRINT.md Section B — informational only, does not
    feed into readiness_engine's score. Purely computed, no AI call."""
    return compute_freshness(
        user_id=request.user_id,
        required_skills=request.required_skills,
        github_evidence=request.github_evidence,
        submission_history=request.submission_history,
    )
