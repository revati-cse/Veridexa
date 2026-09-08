from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.github.client import GithubAccessError
from app.schemas import GithubAnalyzeRequest, GithubAnalyzeResponse
from app.services.github_analyzer import analyze_repository

router = APIRouter(prefix="/github", tags=["github"])


@router.post("/analyze", response_model=GithubAnalyzeResponse)
async def analyze_repository_endpoint(request: GithubAnalyzeRequest) -> GithubAnalyzeResponse:
    """Calls github_analyzer.py (read-only GitHub REST + Claude). A repo we
    can't read (404/private/rate-limited) is a real error — we never show
    fabricated evidence for a repository we never looked at — so it surfaces
    as 422 rather than a 200 with empty data."""
    try:
        languages_detected, skills, claims_vs_evidence, used_fallback = await analyze_repository(
            repository_url=request.repository_url,
            claimed_skills=request.claimed_skills,
            required_skills=request.required_skills,
        )
    except GithubAccessError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return GithubAnalyzeResponse(
        repository_id=uuid4(),
        repository=request.repository_url,
        languages_detected=languages_detected,
        skills=skills,
        claims_vs_evidence=claims_vs_evidence,
        demo_fallback=used_fallback,
    )
