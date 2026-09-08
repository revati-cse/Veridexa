from fastapi import APIRouter

from app.schemas import SubmissionCreate, SubmissionEvaluationResponse
from app.services.evaluation_engine import evaluate_submission

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionEvaluationResponse)
async def create_submission(request: SubmissionCreate) -> SubmissionEvaluationResponse:
    """Calls evaluation_engine.py. The SQL sandbox always runs for real
    against the submitted challenge's dataset; only the AI reasoning pass
    falls back to a fixture if Claude is unavailable."""
    response, _ = await evaluate_submission(request.challenge, request.code, request.explanation)
    return response
