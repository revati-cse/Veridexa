from uuid import UUID

from fastapi import APIRouter

from app.schemas import (
    ChallengeGenerateRequest,
    ChallengeGenerateResponse,
    ChallengeHistoryResponse,
    ChallengeMutateRequest,
    ChallengeMutateResponse,
)
from app.services.challenge_generator import generate_challenge
from app.services.challenge_mutation_engine import mutate_challenge

router = APIRouter(prefix="/challenges", tags=["challenges"])


@router.post("/generate", response_model=ChallengeGenerateResponse)
async def generate_challenge_endpoint(request: ChallengeGenerateRequest) -> ChallengeGenerateResponse:
    """Calls challenge_generator.py (Claude, structured output). Falls back
    to the demo fixture automatically if Claude is unavailable."""
    challenge, used_fallback = await generate_challenge(
        job_id=request.job_id,
        job_title=request.job_title,
        required_skills=request.required_skills,
        difficulty=request.difficulty,
    )
    return ChallengeGenerateResponse(challenge=challenge, demo_fallback=used_fallback)


@router.post("/mutate", response_model=ChallengeMutateResponse)
async def mutate_challenge_endpoint(request: ChallengeMutateRequest) -> ChallengeMutateResponse:
    """Calls challenge_mutation_engine.py — the core product differentiator
    (Feature 8). Falls back to the demo fixture automatically if Claude is
    unavailable; difficulty is always backend-assigned either way."""
    challenge, used_fallback = await mutate_challenge(
        job_id=request.job_id,
        job_title=request.job_title,
        required_skills=request.required_skills,
        previous_attempt=request.previous_attempt,
    )
    return ChallengeMutateResponse(challenge=challenge, demo_fallback=used_fallback)


@router.get("/{challenge_id}/history", response_model=ChallengeHistoryResponse)
async def get_challenge_history(challenge_id: UUID) -> ChallengeHistoryResponse:
    """STUB: real implementation walks parent_challenge_id back to the root."""
    return ChallengeHistoryResponse(chain=[])
