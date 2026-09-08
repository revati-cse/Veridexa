from uuid import uuid4

from fastapi import APIRouter

from app.schemas import JobParseRequest, JobParseResponse
from app.services.job_parser import parse_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/parse", response_model=JobParseResponse)
async def parse_job_endpoint(request: JobParseRequest) -> JobParseResponse:
    """Calls job_parser.py (Claude, structured output). Falls back to the
    demo fixture automatically if Claude is unavailable — demo_fallback on
    the response says which happened. job_id is a fresh uuid for now; DB
    persistence lands once a Supabase project is provisioned."""
    job, used_fallback = await parse_job(request.raw_description)
    return JobParseResponse(job_id=uuid4(), job=job, demo_fallback=used_fallback)
