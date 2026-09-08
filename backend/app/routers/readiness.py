from fastapi import APIRouter

from app.schemas import ReadinessComputeRequest, ReadinessResponse
from app.services.readiness_engine import compute_readiness

router = APIRouter(prefix="/readiness", tags=["readiness"])


@router.post("/compute", response_model=ReadinessResponse)
async def compute_readiness_endpoint(request: ReadinessComputeRequest) -> ReadinessResponse:
    """No DB persistence yet, so readiness is computed directly from the
    session state the frontend already holds (it drove the job/evidence/
    challenge screens) rather than looked up by job_id. Purely computed, no
    AI call — see readiness_engine.py for the weighted-score formula."""
    return compute_readiness(
        user_id=request.user_id,
        job_id=request.job_id,
        job_title=request.job_title,
        required_skills=request.required_skills,
        claims=request.claims,
        github_evidence=request.github_evidence,
        project_description_evidence=request.project_description_evidence,
        submission_history=request.submission_history,
    )
