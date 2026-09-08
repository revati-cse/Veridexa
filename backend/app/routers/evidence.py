from fastapi import APIRouter

from app.schemas import EvidenceComputeRequest, EvidenceListResponse
from app.services.evidence_engine import compute_evidence

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("/compute", response_model=EvidenceListResponse)
async def compute_evidence_endpoint(request: EvidenceComputeRequest) -> EvidenceListResponse:
    """No DB persistence yet, so this takes the accumulated session state
    (GitHub evidence + submission history) directly from the frontend rather
    than looking anything up by user_id. Purely computed, no AI call."""
    return compute_evidence(
        user_id=request.user_id,
        github_evidence=request.github_evidence,
        submission_history=request.submission_history,
    )
