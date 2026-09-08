from uuid import UUID, uuid4

from fastapi import APIRouter

from app.schemas import (
    Challenge,
    ChallengeGenerateRequest,
    ChallengeGenerateResponse,
    ChallengeHistoryResponse,
    ChallengeMutateRequest,
    ChallengeMutateResponse,
)
from app.schemas.evaluation import DEFAULT_RUBRIC_WEIGHTS
from app.services.challenge_generator import generate_challenge

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
async def mutate_challenge(request: ChallengeMutateRequest) -> ChallengeMutateResponse:
    """STUB: returns a fixed mutated scenario until challenge_mutation_engine.py
    (Phase 12 — the core innovation) is wired in."""
    mutated = Challenge(
        id=uuid4(),
        job_id=None,
        parent_challenge_id=request.previous_challenge_id,
        title="Clean Duplicate and Missing-ID Transactions",
        role="Junior Data Analyst",
        scenario=(
            "The finance team has discovered missing customer IDs and duplicate "
            "payment records. Clean the data and determine whether the reported "
            "revenue increase is genuine."
        ),
        instructions="Write a SQL query that deduplicates records and handles NULL customer IDs.",
        required_skills=["SQL", "Statistics"],
        difficulty=2,
        dataset={"tables": ["customers", "orders", "payments"], "seed": "stub_mutated"},
        expected_output="A deduplicated, NULL-safe revenue figure.",
        evaluation_criteria=DEFAULT_RUBRIC_WEIGHTS,
        mutation_reason=(
            "Targeted because your previous submission missed NULL customer_id "
            "handling and did not deduplicate transaction IDs."
        ),
    )
    return ChallengeMutateResponse(challenge=mutated, demo_fallback=True)


@router.get("/{challenge_id}/history", response_model=ChallengeHistoryResponse)
async def get_challenge_history(challenge_id: UUID) -> ChallengeHistoryResponse:
    """STUB: real implementation walks parent_challenge_id back to the root."""
    return ChallengeHistoryResponse(chain=[])
