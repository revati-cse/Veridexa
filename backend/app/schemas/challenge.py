from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import Difficulty


class ChallengeGenerateRequest(BaseModel):
    job_id: UUID
    user_id: UUID
    required_skills: list[str]
    difficulty: Difficulty = 1


class Challenge(BaseModel):
    """Structured output of challenge_generator.py / challenge_mutation_engine.py.

    `dataset` is intentionally `Any` (inline rows or a schema+seed-SQL object) —
    the sql_runner sandbox interprets its shape, this schema only carries it.
    `evaluation_criteria` maps rubric criterion name -> weight (0-1, sums to 1).
    """

    id: UUID
    job_id: UUID | None = None
    parent_challenge_id: UUID | None = None
    title: str
    role: str
    scenario: str
    instructions: str
    required_skills: list[str]
    difficulty: Difficulty
    dataset: Any = None
    expected_output: str | None = None
    evaluation_criteria: dict[str, float]
    mutation_reason: str | None = None


class ChallengeGenerateResponse(BaseModel):
    challenge: Challenge
    demo_fallback: bool = False


class ChallengeMutateRequest(BaseModel):
    previous_challenge_id: UUID
    evaluation_id: UUID
    user_id: UUID


class ChallengeMutateResponse(BaseModel):
    challenge: Challenge
    demo_fallback: bool = False


class ChallengeHistoryResponse(BaseModel):
    """Walks parent_challenge_id back to the root, oldest first."""

    chain: list[Challenge]
