"""recruiter_dashboard service — BLUEPRINT.md Section B (P3, optional).

Aggregates candidates across a job by reusing readiness_engine.compute_readiness
verbatim — a recruiter's number is never computed by different logic than
the candidate's own dashboard uses. Real persisted claims (candidate_claims,
migration 003) now feed into this the same way they would for the
candidate's own session; github_evidence=None remains for every candidate,
since GitHub analysis is still never written to storage (see CLAUDE.md) —
the score reflects challenge performance plus claim alignment, not
repository evidence.

github_evidence=None degrades the same way readiness_engine already
handles a missing component (Section N: the weighted average just excludes
it) — this is not a special case, it's the same formula every other caller
already exercises without GitHub evidence.

Unlike every other engine in this codebase, this one requires a database —
there is no way to know "which candidates applied to this job" from a
single session's state. Returns an empty, `db_available: False` response
rather than raising when no DATABASE_URL is configured.
"""

from uuid import UUID

from app.db.challenges import get_candidate_ids_for_job
from app.db.claims import get_claims
from app.db.jobs import get_job
from app.db.pool import is_available
from app.db.submissions import get_submission_history_for_job
from app.schemas.recruiter import CandidateSummary, RecruiterDashboardResponse
from app.services.readiness_engine import compute_readiness


async def get_dashboard(job_id: UUID) -> RecruiterDashboardResponse:
    if not is_available():
        return RecruiterDashboardResponse(job_id=job_id, job_title="", db_available=False, candidates=[])

    job = await get_job(job_id)
    if job is None:
        return RecruiterDashboardResponse(job_id=job_id, job_title="", db_available=True, candidates=[])

    candidate_ids = await get_candidate_ids_for_job(job_id)

    candidates: list[CandidateSummary] = []
    for user_id in candidate_ids:
        submission_history = await get_submission_history_for_job(job_id, user_id)
        if not submission_history:
            continue  # a challenge row with no completed submission isn't a candidate to rank yet

        claims = await get_claims(user_id)
        readiness = compute_readiness(
            user_id=user_id,
            job_id=job_id,
            job_title=job.title,
            required_skills=job.required_skills,
            claims=claims,
            github_evidence=None,
            submission_history=submission_history,
        )
        candidates.append(
            CandidateSummary(
                user_id=user_id,
                readiness_score=readiness.readiness_score,
                challenges_completed=len(submission_history),
                strengths=readiness.strengths,
                weaknesses=readiness.weaknesses,
                skill_gaps=readiness.skill_gaps,
                skill_breakdown=readiness.skill_breakdown,
            )
        )

    candidates.sort(key=lambda c: c.readiness_score, reverse=True)
    return RecruiterDashboardResponse(job_id=job_id, job_title=job.title, db_available=True, candidates=candidates)
