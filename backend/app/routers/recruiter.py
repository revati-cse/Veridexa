from uuid import UUID

from fastapi import APIRouter

from app.schemas.recruiter import RecruiterDashboardResponse
from app.services.recruiter_dashboard import get_dashboard

router = APIRouter(prefix="/recruiter", tags=["recruiter"])


@router.get("/jobs/{job_id}/dashboard", response_model=RecruiterDashboardResponse)
async def get_recruiter_dashboard(job_id: UUID) -> RecruiterDashboardResponse:
    """P3/optional per BLUEPRINT.md Section B — the one endpoint in this API
    that requires a database (see recruiter_dashboard.py's docstring). No
    auth: this app has no recruiter/candidate role distinction at all
    (Section T explicitly scopes auth out of the hackathon build)."""
    return await get_dashboard(job_id)
