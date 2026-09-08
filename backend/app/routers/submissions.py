from uuid import uuid4

from fastapi import APIRouter

from app.schemas import (
    EvidenceObservation,
    SkillGapItem,
    SqlExecutionResult,
    SubmissionCreate,
    SubmissionEvaluationResponse,
)

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionEvaluationResponse)
async def create_submission(request: SubmissionCreate) -> SubmissionEvaluationResponse:
    """STUB: skips the real sql_runner sandbox + evaluation prompt (Phase 8)
    and returns a fixed, schema-valid evaluation so Screen 6 can be built now.

    overall_score below is pre-computed by hand as
    Σ(criterion_score × weight) to keep the stub honest about the rule that
    the LLM never sets the total — evaluation_engine.py will do this same
    arithmetic in code once it exists.
    """
    rubric_scores = {
        "correctness": 85.0,
        "technical_logic": 80.0,
        "reasoning": 70.0,
        "edge_cases": 55.0,
        "efficiency": 75.0,
    }
    weights = {
        "correctness": 0.3, "technical_logic": 0.25, "reasoning": 0.2,
        "edge_cases": 0.15, "efficiency": 0.1,
    }
    overall_score = round(sum(rubric_scores[k] * weights[k] for k in weights), 2)

    return SubmissionEvaluationResponse(
        submission_id=uuid4(),
        evaluation_id=uuid4(),
        rubric_scores=rubric_scores,
        overall_score=overall_score,
        strengths=["Correct use of JOIN across customers/orders/payments", "Clear query structure"],
        weaknesses=["Did not handle NULL customer_id values", "Missed duplicate transaction IDs"],
        evidence=[
            EvidenceObservation(skill="SQL", observation="Correct JOIN and GROUP BY usage", confidence=0.85),
        ],
        skill_gaps=[
            SkillGapItem(skill="Statistics", missing_concepts=["Hypothesis testing", "Statistical significance"]),
        ],
        sql_execution_result=SqlExecutionResult(
            success=True, columns=["month", "revenue"], rows=[["2026-01", 48210]], row_count=1,
        ),
        demo_fallback=True,
    )
