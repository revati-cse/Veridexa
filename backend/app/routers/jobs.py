from uuid import uuid4

from fastapi import APIRouter

from app.db import safe_write
from app.db.jobs import save_job
from app.schemas import JobParseRequest, JobParseResponse
from app.services.job_parser import parse_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/parse", response_model=JobParseResponse)
async def parse_job_endpoint(request: JobParseRequest) -> JobParseResponse:
    """Calls job_parser.py (Claude, structured output). Falls back to the
    demo fixture automatically if Claude is unavailable — demo_fallback on
    the response says which happened. job_id is minted here (not read back
    from the DB) so the response never blocks on persistence succeeding."""
    job, used_fallback = await parse_job(request.raw_description)
    job_id = uuid4()
    await safe_write(save_job(job_id, request.raw_description, job))
    return JobParseResponse(job_id=job_id, job=job, demo_fallback=used_fallback)
