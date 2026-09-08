from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import Difficulty
from app.schemas.sandbox import SandboxDataset


class ChallengeGenerateRequest(BaseModel):
    job_id: UUID
    # No DB persistence yet, so the frontend passes the title it already has
    # in its session store rather than the backend looking it up by job_id.
    job_title: str
    user_id: UUID
    required_skills: list[str]
    difficulty: Difficulty = 1


class ChallengeAIOutput(BaseModel):
    """What Claude actually returns from challenge_generation_prompt.py.
    `difficulty` and `evaluation_criteria` are deliberately absent — both are
    backend-assigned (Section K/3), never LLM-authored. `dataset` reuses the
    sql_runner sandbox's own schema, so a generated challenge is guaranteed
    to be runnable by construction rather than merely schema-shaped."""

    title: str
    role: str
    scenario: str
    instructions: str
    required_skills: list[str]
    dataset: SandboxDataset
    expected_output: str


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
