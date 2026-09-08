from uuid import uuid4

from fastapi import APIRouter

from app.schemas import (
    EvidenceComputeRequest,
    EvidenceListResponse,
    ProjectDescriptionAnalyzeRequest,
    ProjectDescriptionAnalyzeResponse,
)
from app.services.evidence_engine import compute_evidence
from app.services.project_description_analyzer import analyze_description

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("/compute", response_model=EvidenceListResponse)
async def compute_evidence_endpoint(request: EvidenceComputeRequest) -> EvidenceListResponse:
    """No DB persistence yet, so this takes the accumulated session state
    (GitHub evidence, project-description evidence, submission history)
    directly from the frontend rather than looking anything up by user_id.
    Purely computed, no AI call."""
    return compute_evidence(
        user_id=request.user_id,
        github_evidence=request.github_evidence,
        project_description_evidence=request.project_description_evidence,
        submission_history=request.submission_history,
    )


@router.post("/analyze-description", response_model=ProjectDescriptionAnalyzeResponse)
async def analyze_description_endpoint(
    request: ProjectDescriptionAnalyzeRequest,
) -> ProjectDescriptionAnalyzeResponse:
    """The evidence path for a candidate with a project but no repository
    link — see project_description_analyzer.py."""
    skills, claims_vs_evidence, used_fallback = await analyze_description(
        description=request.description,
        claimed_skills=request.claimed_skills,
        required_skills=request.required_skills,
    )
    return ProjectDescriptionAnalyzeResponse(
        source_id=uuid4(),
        skills=skills,
        claims_vs_evidence=claims_vs_evidence,
        demo_fallback=used_fallback,
    )
