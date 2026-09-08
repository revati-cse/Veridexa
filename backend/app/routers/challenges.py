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

router = APIRouter(prefix="/challenges", tags=["challenges"])

_RUBRIC_WEIGHTS = {
    "correctness": 0.3,
    "technical_logic": 0.25,
    "reasoning": 0.2,
    "edge_cases": 0.15,
    "efficiency": 0.1,
}


def _stub_challenge(request: ChallengeGenerateRequest) -> Challenge:
    return Challenge(
        id=uuid4(),
        job_id=request.job_id,
        parent_challenge_id=None,
        title="Investigate the Revenue Discrepancy",
        role="Junior Data Analyst",
        scenario=(
            "The finance team reports that monthly revenue looks inflated. "
            "You are given customer, order, and payment tables."
        ),
        instructions="Write a SQL query that identifies the source of the discrepancy.",
        required_skills=request.required_skills or ["SQL"],
        difficulty=request.difficulty,
        dataset={"tables": ["customers", "orders", "payments"], "seed": "stub"},
        expected_output="A corrected revenue figure with the root cause explained.",
        evaluation_criteria=_RUBRIC_WEIGHTS,
        mutation_reason=None,
    )


@router.post("/generate", response_model=ChallengeGenerateResponse)
async def generate_challenge(request: ChallengeGenerateRequest) -> ChallengeGenerateResponse:
    """STUB: returns a fixed scenario until challenge_generator.py (Phase 9) is wired in."""
    return ChallengeGenerateResponse(challenge=_stub_challenge(request), demo_fallback=True)


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
        evaluation_criteria=_RUBRIC_WEIGHTS,
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
