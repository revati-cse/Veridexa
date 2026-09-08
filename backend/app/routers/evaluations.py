from uuid import UUID, uuid4

from fastapi import APIRouter

from app.schemas import SubmissionEvaluationResponse

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/{evaluation_id}", response_model=SubmissionEvaluationResponse)
async def get_evaluation(evaluation_id: UUID) -> SubmissionEvaluationResponse:
    """STUB: /submissions returns its evaluation inline (Section G); this
    endpoint exists only for re-fetching a past evaluation by id, e.g. when
    rendering challenge history. Not on the critical path for the demo loop."""
    return SubmissionEvaluationResponse(
        submission_id=uuid4(),
        evaluation_id=evaluation_id,
        rubric_scores={"correctness": 85.0, "technical_logic": 80.0, "reasoning": 70.0, "edge_cases": 55.0, "efficiency": 75.0},
        overall_score=76.0,
        strengths=[], weaknesses=[], evidence=[], skill_gaps=[],
        sql_execution_result=None,
        demo_fallback=True,
    )
