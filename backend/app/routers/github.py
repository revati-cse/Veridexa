from uuid import uuid4

from fastapi import APIRouter

from app.schemas import (
    ClaimVsEvidenceItem,
    GithubAnalyzeRequest,
    GithubAnalyzeResponse,
    LanguageDetected,
    SkillEvidenceItem,
)

router = APIRouter(prefix="/github", tags=["github"])


@router.post("/analyze", response_model=GithubAnalyzeResponse)
async def analyze_repository(request: GithubAnalyzeRequest) -> GithubAnalyzeResponse:
    """STUB: returns fixed repository evidence until github_analyzer.py
    (Phase 5A) implements the real fetch/filter/rank/analyze pipeline."""
    return GithubAnalyzeResponse(
        repository_id=uuid4(),
        repository=request.repository_url,
        languages_detected=[
            LanguageDetected(language="Python", confidence=0.82),
            LanguageDetected(language="SQL", confidence=0.14),
        ],
        skills=[
            SkillEvidenceItem(
                skill="Python",
                evidence_strength="strong",
                confidence=0.91,
                observations=["Multiple Python modules", "Pandas data processing"],
            ),
            SkillEvidenceItem(
                skill="SQL",
                evidence_strength="moderate",
                confidence=0.6,
                observations=["JOIN and GROUP BY usage in query files"],
            ),
        ],
        claims_vs_evidence=[
            ClaimVsEvidenceItem(
                skill="Python", claim="advanced",
                repository_evidence="strong", assessment="Strong evidence supports this claim",
            ),
            ClaimVsEvidenceItem(
                skill="SQL", claim="advanced",
                repository_evidence="moderate",
                assessment="Partially supported — verify via challenge",
            ),
        ],
        demo_fallback=True,
    )
