from uuid import uuid4

from fastapi import APIRouter

from app.schemas import JobParseRequest, JobParseResponse, JobRequiredSkill, ParsedJob

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/parse", response_model=JobParseResponse)
async def parse_job(request: JobParseRequest) -> JobParseResponse:
    """STUB: returns a fixed structured job until job_parser.py (Phase 3) is wired in.

    Proves the request/response contract end-to-end so the frontend can build
    Screens 2/3 against a stable shape before the Claude call exists.
    """
    stub_job = ParsedJob(
        title="Data Analyst",
        required_skills=[
            JobRequiredSkill(skill="SQL", importance="high"),
            JobRequiredSkill(skill="Python", importance="high"),
            JobRequiredSkill(skill="Statistics", importance="medium"),
            JobRequiredSkill(skill="Power BI", importance="medium"),
            JobRequiredSkill(skill="Problem Solving", importance="high"),
        ],
        soft_skills=["Communication", "Attention to detail"],
        tools=["Excel", "Power BI"],
        experience_years=1,
    )
    return JobParseResponse(job_id=uuid4(), job=stub_job, demo_fallback=True)
