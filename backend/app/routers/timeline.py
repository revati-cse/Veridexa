from fastapi import APIRouter

from app.schemas.timeline import TimelineComputeRequest, TimelineResponse
from app.services.timeline_engine import compute_timeline

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.post("/compute", response_model=TimelineResponse)
async def compute_timeline_endpoint(request: TimelineComputeRequest) -> TimelineResponse:
    """P3/optional per BLUEPRINT.md Section B — purely computed, no AI call,
    no DB read required."""
    return compute_timeline(user_id=request.user_id, submission_history=request.submission_history)
