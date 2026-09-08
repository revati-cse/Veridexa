"""evaluation_engine service — BLUEPRINT.md Feature 4.

Hybrid evaluation per Section 15: sql_runner always runs for real against
the challenge's own dataset — it is never skipped or faked, even on the
Claude-fallback path — and its result is passed to the evaluation prompt as
ground truth. overall_score is always Σ(criterion_score × weight), computed
here in code from the challenge's evaluation_criteria; the LLM never sets
the total.
"""

import json
import logging
from pathlib import Path
from uuid import uuid4

from app.ai.claude_client import AIServiceUnavailable, call_structured
from app.ai.prompts.evaluation_prompt import SYSTEM_PROMPT, build_user_prompt
from app.sandbox.sql_runner import run_sql
from app.schemas.challenge import Challenge
from app.schemas.evaluation import EvaluationResult, SqlExecutionResult, SubmissionEvaluationResponse

logger = logging.getLogger(__name__)

_FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "demo_evaluation.json"


def _load_fixture() -> EvaluationResult:
    data = json.loads(_FIXTURE_PATH.read_text())
    return EvaluationResult.model_validate(data)


def _compute_overall_score(rubric_scores: dict[str, float], weights: dict[str, float]) -> float:
    total = sum(rubric_scores.get(criterion, 0.0) * weight for criterion, weight in weights.items())
    return round(total, 2)


def _run_sandbox(code: str, dataset: object) -> SqlExecutionResult:
    if not code.strip():
        return SqlExecutionResult(success=False, rejected_reason="No SQL was submitted.")
    return run_sql(code, dataset)


async def evaluate_submission(
    challenge: Challenge,
    code: str,
    explanation: str,
) -> tuple[SubmissionEvaluationResponse, bool]:
    """Returns (response, used_ai_fallback)."""
    sql_result = _run_sandbox(code, challenge.dataset)

    try:
        ai_result = await call_structured(
            system=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(challenge, code, explanation, sql_result),
            response_model=EvaluationResult,
        )
        used_fallback = False
    except AIServiceUnavailable as exc:
        logger.warning("evaluation_engine falling back to fixture: %s", exc)
        ai_result = _load_fixture()
        used_fallback = True

    rubric_scores = ai_result.rubric_scores.model_dump()
    overall_score = _compute_overall_score(rubric_scores, challenge.evaluation_criteria)

    response = SubmissionEvaluationResponse(
        submission_id=uuid4(),
        evaluation_id=uuid4(),
        rubric_scores=rubric_scores,
        overall_score=overall_score,
        strengths=ai_result.strengths,
        weaknesses=ai_result.weaknesses,
        evidence=ai_result.evidence,
        skill_gaps=ai_result.skill_gaps,
        sql_execution_result=sql_result,
        demo_fallback=used_fallback,
    )
    return response, used_fallback
