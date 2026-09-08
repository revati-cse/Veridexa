from uuid import UUID

from fastapi import APIRouter

from app.db import safe_write
from app.db.challenges import get_challenge_chain, save_challenge
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
    await safe_write(save_challenge(challenge, request.user_id))
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
    # The previous attempt's challenge may not have been persisted yet (e.g.
    # DB was down when it was generated) — save it too so parent_challenge_id
    # resolves for the history walk.
    await safe_write(save_challenge(request.previous_attempt.challenge, request.user_id))
    await safe_write(save_challenge(challenge, request.user_id))
    return ChallengeMutateResponse(challenge=challenge, demo_fallback=used_fallback)


@router.get("/{challenge_id}/history", response_model=ChallengeHistoryResponse)
async def get_challenge_history(challenge_id: UUID) -> ChallengeHistoryResponse:
    """Walks parent_challenge_id back to the root via the DB. Returns an
    empty chain (not an error) when no database is configured or the
    challenge was never persisted — this view is a nice-to-have, not a
    critical path."""
    chain = await get_challenge_chain(challenge_id)
    return ChallengeHistoryResponse(chain=chain)
