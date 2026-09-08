from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.challenge import Challenge

# Default SQL/data-challenge rubric (BLUEPRINT.md Section K). Backend-assigned
# and shared by challenge_generator.py and evaluation_engine.py — the LLM is
# never asked to invent rubric weights, so they're guaranteed to sum to 1.0.
DEFAULT_RUBRIC_WEIGHTS: dict[str, float] = {
    "correctness": 0.30,
    "technical_logic": 0.25,
    "reasoning": 0.20,
    "edge_cases": 0.15,
    "efficiency": 0.10,
}


class SqlExecutionResult(BaseModel):
    """Ground truth produced by sandbox/sql_runner.py, fed into the evaluation
    prompt as grounding — the LLM never re-derives correctness on its own."""

    success: bool
    columns: list[str] = []
    rows: list[list] = []
    row_count: int = 0
    error: str | None = None
    rejected_reason: str | None = None  # set if statement failed the denylist check


class EvidenceObservation(BaseModel):
    skill: str
    observation: str
    confidence: float = Field(ge=0, le=1)


class SkillGapItem(BaseModel):
    skill: str
    missing_concepts: list[str] = []


class RubricScores(BaseModel):
    """Exactly the 5 criteria in DEFAULT_RUBRIC_WEIGHTS. A strict model
    rather than a loose dict, so a missing or misnamed criterion in Claude's
    output fails Pydantic validation (caught by claude_client's retry-then-
    fallback) instead of silently contributing 0 to the weighted
    overall_score — a wrong-key bug here would otherwise be invisible."""

    correctness: float = Field(ge=0, le=100)
    technical_logic: float = Field(ge=0, le=100)
    reasoning: float = Field(ge=0, le=100)
    edge_cases: float = Field(ge=0, le=100)
    efficiency: float = Field(ge=0, le=100)


class EvaluationResult(BaseModel):
    """Raw structured output of the evaluation prompt (Claude), BEFORE backend
    weighting is applied."""

    rubric_scores: RubricScores
    strengths: list[str] = []
    weaknesses: list[str] = []
    evidence: list[EvidenceObservation] = []
    skill_gaps: list[SkillGapItem] = []


class SubmissionEvaluationResponse(BaseModel):
    """Returned by POST /submissions — the persisted evaluation row, with
    overall_score computed backend-side (Section K), never by the LLM."""

    submission_id: UUID
    evaluation_id: UUID
    rubric_scores: dict[str, float]
    overall_score: float = Field(ge=0, le=100)
    strengths: list[str]
    weaknesses: list[str]
    evidence: list[EvidenceObservation]
    skill_gaps: list[SkillGapItem]
    sql_execution_result: SqlExecutionResult | None = None
    demo_fallback: bool = False
    # Set server-side when this response is built (never client-supplied) —
    # freshness_engine.py's only signal for "how current is this evidence".
    # Round-trips unchanged once the frontend passes this response back into
    # a later request (e.g. nested in a SubmissionRecord).
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SubmissionRecord(BaseModel):
    """One completed challenge attempt — the challenge plus the evaluation it
    received. No DB persistence exists yet, so the frontend accumulates
    these in its session store (BLUEPRINT.md Section D) as the candidate
    completes challenges, and passes the full history to evidence_engine.py
    and readiness_engine.py so multi-round scoring (e.g. after a mutation
    improves a weak skill) works without a database to query."""

    challenge: Challenge
    evaluation: SubmissionEvaluationResponse


class ChallengeMutateRequest(BaseModel):
    """No DB persistence yet — the frontend already holds the full previous
    Challenge + its evaluation (as a SubmissionRecord) from the screens it
    already passed through, so it's sent directly rather than by id. Lives
    here rather than in schemas/challenge.py because it needs SubmissionRecord,
    and challenge.py must stay import-safe from evaluation.py (which already
    imports Challenge from challenge.py) to avoid a circular import."""

    user_id: UUID
    job_id: UUID
    job_title: str
    required_skills: list[str]
    previous_attempt: SubmissionRecord
