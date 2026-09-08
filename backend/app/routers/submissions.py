from fastapi import APIRouter

from app.db import safe_write
from app.db.evidence import save_evidence_rows
from app.db.submissions import save_submission_and_evaluation
from app.schemas import SubmissionCreate, SubmissionEvaluationResponse
from app.schemas.evaluation import SubmissionRecord
from app.services.evaluation_engine import evaluate_submission
from app.services.evidence_engine import build_evidence_rows

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionEvaluationResponse)
async def create_submission(request: SubmissionCreate) -> SubmissionEvaluationResponse:
    """Calls evaluation_engine.py. The SQL sandbox always runs for real
    against the submitted challenge's dataset; only the AI reasoning pass
    falls back to a fixture if Claude is unavailable."""
    response, _ = await evaluate_submission(request.challenge, request.code, request.explanation)

    await safe_write(
        save_submission_and_evaluation(
            request.challenge, request.user_id, request.code, request.explanation, response
        )
    )
    evidence_rows = build_evidence_rows(
        github_evidence=None,
        submission_history=[SubmissionRecord(challenge=request.challenge, evaluation=response)],
    )
    await safe_write(
        save_evidence_rows(evidence_rows, request.user_id, challenge_id=request.challenge.id)
    )

    return response
