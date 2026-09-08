"""Integration tests for recruiter_dashboard.py against a real local
Postgres instance — this feature has no "compute from session state"
fallback (see the module's own docstring), so unlike every other engine in
this codebase it can only be tested against a real database, not mocked.
Follows the same db_test pattern as test_db_persistence.py; skipped
entirely (not failed) when no reachable Postgres is configured.
"""

import asyncio
import os
from functools import wraps
from uuid import uuid4

import asyncpg
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.db import pool as db_pool
from app.db.challenges import save_challenge
from app.db.jobs import save_job
from app.db.submissions import save_submission_and_evaluation
from app.main import app
from app.schemas.challenge import Challenge
from app.schemas.evaluation import SubmissionEvaluationResponse
from app.schemas.job import JobRequiredSkill, ParsedJob
from app.services.recruiter_dashboard import get_dashboard

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://veridexa:veridexa_dev@localhost:5432/veridexa"
)


def _db_reachable() -> bool:
    async def _check() -> bool:
        try:
            conn = await asyncpg.connect(TEST_DATABASE_URL, timeout=2)
        except Exception:
            return False
        await conn.close()
        return True

    return asyncio.run(_check())


pytestmark = pytest.mark.skipif(
    not _db_reachable(),
    reason="No reachable local Postgres configured (TEST_DATABASE_URL) for DB integration tests",
)


def db_test(test_fn):
    @wraps(test_fn)
    def wrapper(*args, **kwargs):
        async def runner():
            settings.database_url = TEST_DATABASE_URL
            await db_pool.connect()
            try:
                await test_fn(*args, **kwargs)
            finally:
                await db_pool.disconnect()
                settings.database_url = ""

        asyncio.run(runner())

    return wrapper


async def _execute(query: str, *args):
    async with db_pool.acquire() as conn:
        await conn.execute(query, *args)


def _challenge(job_id, **overrides) -> Challenge:
    fields = dict(
        id=uuid4(), job_id=job_id, parent_challenge_id=None,
        title="Investigate the Revenue Discrepancy", role="Junior Data Analyst",
        scenario="Revenue looks inflated.", instructions="Write a query.",
        required_skills=["SQL"], difficulty=1, dataset={"tables": []},
        expected_output="Revenue per customer.",
        evaluation_criteria={
            "correctness": 0.3, "technical_logic": 0.25, "reasoning": 0.2,
            "edge_cases": 0.15, "efficiency": 0.1,
        },
        mutation_reason=None,
    )
    fields.update(overrides)
    return Challenge(**fields)


def _evaluation(overall_score: float) -> SubmissionEvaluationResponse:
    return SubmissionEvaluationResponse(
        submission_id=uuid4(), evaluation_id=uuid4(),
        rubric_scores={"correctness": 80, "technical_logic": 80, "reasoning": 80, "edge_cases": 80, "efficiency": 80},
        overall_score=overall_score, strengths=[], weaknesses=[], evidence=[], skill_gaps=[],
        sql_execution_result=None, demo_fallback=False,
    )


async def _cleanup(job_id, user_ids):
    for user_id in user_ids:
        await _execute("DELETE FROM users WHERE id = $1", user_id)
    await _execute("DELETE FROM jobs WHERE id = $1", job_id)


@db_test
async def test_dashboard_returns_empty_for_unknown_job():
    response = await get_dashboard(uuid4())
    assert response.db_available is True
    assert response.candidates == []


@db_test
async def test_dashboard_ranks_candidates_by_readiness_score_descending():
    job_id = uuid4()
    strong_candidate, weak_candidate = uuid4(), uuid4()
    try:
        await save_job(
            job_id, "raw jd text",
            ParsedJob(title="Data Analyst", required_skills=[JobRequiredSkill(skill="SQL", importance="high")]),
        )

        strong_challenge = _challenge(job_id)
        await save_submission_and_evaluation(strong_challenge, strong_candidate, "SELECT 1", "x", _evaluation(90.0))

        weak_challenge = _challenge(job_id, id=uuid4())
        await save_submission_and_evaluation(weak_challenge, weak_candidate, "SELECT 1", "x", _evaluation(40.0))

        response = await get_dashboard(job_id)

        assert response.db_available is True
        assert response.job_title == "Data Analyst"
        assert [c.user_id for c in response.candidates] == [strong_candidate, weak_candidate]
        assert response.candidates[0].readiness_score > response.candidates[1].readiness_score
        assert all(c.challenges_completed == 1 for c in response.candidates)

        # skill_breakdown carries the same per-skill rows compute_readiness
        # produces — this is what a candidate-comparison view is built from.
        strong_breakdown = response.candidates[0].skill_breakdown
        assert [row.skill for row in strong_breakdown] == ["SQL"]
        assert strong_breakdown[0].score == response.candidates[0].readiness_score
    finally:
        await _cleanup(job_id, [strong_candidate, weak_candidate])


@db_test
async def test_dashboard_excludes_a_candidate_with_a_challenge_but_no_submission():
    job_id = uuid4()
    submitted_candidate, non_submitting_candidate = uuid4(), uuid4()
    try:
        await save_job(
            job_id, "raw jd text",
            ParsedJob(title="Data Analyst", required_skills=[JobRequiredSkill(skill="SQL", importance="high")]),
        )
        await save_submission_and_evaluation(
            _challenge(job_id), submitted_candidate, "SELECT 1", "x", _evaluation(70.0)
        )
        # A challenge exists for this candidate (e.g. generated but never submitted) —
        # get_candidate_ids_for_job would surface them, but they shouldn't be ranked.
        await save_challenge(_challenge(job_id, id=uuid4()), non_submitting_candidate)

        response = await get_dashboard(job_id)

        assert [c.user_id for c in response.candidates] == [submitted_candidate]
    finally:
        await _cleanup(job_id, [submitted_candidate, non_submitting_candidate])


def test_recruiter_dashboard_endpoint_reflects_the_same_data_over_http():
    # TestClient drives the ASGI app in its own thread with its own event
    # loop (via its blocking portal) — sharing the asyncpg pool from this
    # test's own asyncio.run() call across that boundary raises
    # "another operation is in progress". So this test lets the app's own
    # lifespan (triggered by `with TestClient(app)`) own the pool for its
    # duration instead of the db_test wrapper the other tests here use.
    candidate = uuid4()
    settings.database_url = TEST_DATABASE_URL
    job_id = None
    try:
        with TestClient(app) as client:
            # job_id must come from a real /jobs/parse call (not a random
            # uuid) so the job row actually exists — otherwise save_challenge's
            # FK-violation fallback silently saves the challenge unlinked
            # (job_id=NULL), and it would never show up under this job_id.
            parsed = client.post("/jobs/parse", json={"raw_description": "We need a Data Analyst with SQL skills."})
            assert parsed.status_code == 200
            job_id = parsed.json()["job_id"]
            job_title = parsed.json()["job"]["title"]

            gen = client.post(
                "/challenges/generate",
                json={
                    "job_id": job_id, "job_title": job_title, "user_id": str(candidate),
                    "required_skills": ["SQL"], "difficulty": 1,
                },
            )
            assert gen.status_code == 200
            challenge = gen.json()["challenge"]
            sub = client.post(
                "/submissions",
                json={"challenge": challenge, "user_id": str(candidate), "code": "SELECT 1", "explanation": "x"},
            )
            assert sub.status_code == 200

            response = client.get(f"/recruiter/jobs/{job_id}/dashboard")

            assert response.status_code == 200
            body = response.json()
            assert body["db_available"] is True
            assert len(body["candidates"]) == 1
            assert body["candidates"][0]["user_id"] == str(candidate)
    finally:
        settings.database_url = ""

        async def _cleanup_direct() -> None:
            conn = await asyncpg.connect(TEST_DATABASE_URL)
            try:
                await conn.execute("DELETE FROM users WHERE id = $1", candidate)
                if job_id is not None:
                    await conn.execute("DELETE FROM jobs WHERE id = $1", job_id)
            finally:
                await conn.close()

        asyncio.run(_cleanup_direct())


def test_dashboard_reports_db_unavailable_with_no_database_configured():
    async def _run():
        assert db_pool.is_available() is False
        response = await get_dashboard(uuid4())
        assert response.db_available is False
        assert response.candidates == []

    asyncio.run(_run())
