"""Integration tests for app/db/* against a real local Postgres instance.

Unlike every other test in this suite, these hit a real database rather than
mocking it — the goal is to prove the SQL in app/db/*.py actually runs
against the migrated schema (supabase/migrations/001_init.sql), not just
that it's syntactically plausible Python. They skip entirely (not fail) when
no reachable Postgres is configured, since most environments running this
suite won't have one; the DB-unavailable path (is_available() == False) is
already covered elsewhere by every function's own early return, which these
tests also spot-check.

Each test drives its DB work through a single asyncio.run() call so the
asyncpg pool never crosses event loops, and cleans up its own rows by id
afterwards since this is a real, shared database rather than a fixture.
"""

import asyncio
import os
from datetime import datetime, timezone
from functools import wraps
from uuid import uuid4

import asyncpg
import pytest

from app.config import settings
from app.db import pool as db_pool
from app.db.challenges import get_challenge, get_challenge_chain, save_challenge
from app.db.evidence import save_evidence_rows
from app.db.github import save_repository_analysis
from app.db.jobs import get_job, save_job
from app.db.skills import get_taxonomy
from app.db.submissions import save_submission_and_evaluation
from app.db.users import ensure_user
from app.schemas.challenge import Challenge
from app.schemas.evaluation import SubmissionEvaluationResponse
from app.schemas.evidence import EvidenceItem
from app.schemas.github import LanguageDetected, SkillEvidenceItem
from app.schemas.job import JobRequiredSkill, ParsedJob

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
    """Runs an async test body inside one event loop, with `settings`
    pointed at the test database for the duration — mirrors the connect/
    disconnect lifecycle main.py's lifespan drives in the real app."""

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


async def _fetchval(query: str, *args):
    async with db_pool.acquire() as conn:
        return await conn.fetchval(query, *args)


async def _execute(query: str, *args):
    async with db_pool.acquire() as conn:
        await conn.execute(query, *args)


def _default_challenge(**overrides) -> Challenge:
    fields = dict(
        id=uuid4(),
        job_id=None,
        parent_challenge_id=None,
        title="Investigate the Revenue Discrepancy",
        role="Junior Data Analyst",
        scenario="Revenue looks inflated.",
        instructions="Write a query that computes revenue per customer.",
        required_skills=["SQL"],
        difficulty=1,
        dataset={"tables": []},
        expected_output="Revenue per customer.",
        evaluation_criteria={
            "correctness": 0.3, "technical_logic": 0.25, "reasoning": 0.2,
            "edge_cases": 0.15, "efficiency": 0.1,
        },
        mutation_reason=None,
    )
    fields.update(overrides)
    return Challenge(**fields)


@db_test
async def test_get_taxonomy_returns_all_seeded_skills():
    taxonomy = await get_taxonomy()
    assert taxonomy is not None
    assert len(taxonomy) == 44
    assert any(item.name == "SQL" for item in taxonomy)


@db_test
async def test_ensure_user_is_idempotent():
    user_id = uuid4()
    try:
        await ensure_user(user_id)
        await ensure_user(user_id)  # must not raise on the second insert
        count = await _fetchval("SELECT count(*) FROM users WHERE id = $1", user_id)
        assert count == 1
    finally:
        await _execute("DELETE FROM users WHERE id = $1", user_id)


@db_test
async def test_save_and_get_job_round_trips_and_skips_unknown_skills():
    job_id = uuid4()
    try:
        job = ParsedJob(
            title="Data Analyst",
            required_skills=[
                JobRequiredSkill(skill="SQL", importance="high"),
                JobRequiredSkill(skill="Not A Real Skill", importance="low"),
            ],
        )
        await save_job(job_id, "raw jd text", job)

        fetched = await get_job(job_id)

        assert fetched is not None
        assert fetched.title == "Data Analyst"
        # only "SQL" is in the taxonomy — the unknown skill is silently
        # skipped rather than raising, matching save_job's documented
        # behavior for names outside the fixed taxonomy.
        assert [s.skill for s in fetched.required_skills] == ["SQL"]
        assert fetched.required_skills[0].importance == "high"
    finally:
        await _execute("DELETE FROM jobs WHERE id = $1", job_id)

    assert await get_job(job_id) is None


@db_test
async def test_save_challenge_and_walk_history_chain():
    user_id = uuid4()
    root = _default_challenge()
    mutated = _default_challenge(
        id=uuid4(), parent_challenge_id=root.id, mutation_reason="weak on edge cases"
    )
    try:
        await ensure_user(user_id)
        await save_challenge(root, user_id)
        await save_challenge(mutated, user_id)

        chain = await get_challenge_chain(mutated.id)

        assert [c.id for c in chain] == [root.id, mutated.id]
        assert chain[1].mutation_reason == "weak on edge cases"

        fetched_root = await get_challenge(root.id)
        assert fetched_root is not None
        assert fetched_root.title == root.title

        assert await get_challenge(uuid4()) is None
    finally:
        await _execute("DELETE FROM users WHERE id = $1", user_id)


@db_test
async def test_save_submission_and_evaluation_upserts_challenge_and_persists_rows():
    user_id = uuid4()
    challenge = _default_challenge()
    response = SubmissionEvaluationResponse(
        submission_id=uuid4(),
        evaluation_id=uuid4(),
        rubric_scores={
            "correctness": 90.0, "technical_logic": 80.0, "reasoning": 70.0,
            "edge_cases": 60.0, "efficiency": 85.0,
        },
        overall_score=79.5,
        strengths=["clean join"],
        weaknesses=["no null handling"],
        evidence=[],
        skill_gaps=[],
        sql_execution_result=None,
    )
    try:
        # challenge was never saved before this call — save_submission_and_
        # evaluation must upsert it so the submissions FK is satisfied.
        await save_submission_and_evaluation(challenge, user_id, "SELECT 1", "explanation", response)

        challenge_row = await get_challenge(challenge.id)
        assert challenge_row is not None

        submission_score = await _fetchval(
            "SELECT overall_score FROM evaluations WHERE id = $1", response.evaluation_id
        )
        assert float(submission_score) == 79.5

        submission_code = await _fetchval(
            "SELECT code FROM submissions WHERE id = $1", response.submission_id
        )
        assert submission_code == "SELECT 1"
    finally:
        await _execute("DELETE FROM users WHERE id = $1", user_id)


@db_test
async def test_save_repository_analysis_skips_none_evidence_strength():
    user_id = uuid4()
    repository_id = uuid4()
    try:
        await save_repository_analysis(
            repository_id,
            user_id,
            "https://github.com/example/repo",
            languages_detected=[LanguageDetected(language="Python", confidence=0.9)],
            skills=[
                SkillEvidenceItem(skill="Python", evidence_strength="strong", confidence=0.8, observations=["uses type hints"]),
                SkillEvidenceItem(skill="SQL", evidence_strength="none", confidence=0.0, observations=[]),
            ],
        )

        repo_url = await _fetchval("SELECT url FROM repositories WHERE id = $1", repository_id)
        assert repo_url == "https://github.com/example/repo"

        evidence_count = await _fetchval(
            "SELECT count(*) FROM repository_evidence WHERE repository_id = $1", repository_id
        )
        # only the "strong" Python row should have landed — "none" has no
        # row to store (it would violate the table's CHECK constraint).
        assert evidence_count == 1
    finally:
        await _execute("DELETE FROM users WHERE id = $1", user_id)


@db_test
async def test_save_evidence_rows_skips_skills_outside_taxonomy():
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    rows = [
        EvidenceItem(
            id=uuid4(), skill="Python", source_type="github", source_reference="repo",
            observation="uses type hints", confidence=0.8, created_at=now,
        ),
        EvidenceItem(
            id=uuid4(), skill="Not A Real Skill", source_type="github", source_reference="repo",
            observation="n/a", confidence=0.5, created_at=now,
        ),
    ]
    try:
        # repository_id/challenge_id are left None here (both columns are
        # nullable FKs) — a random uuid would violate the FK constraint
        # since no such repository row exists; save_repository_analysis's
        # own test above already covers the case where it does.
        await save_evidence_rows(rows, user_id)

        count = await _fetchval("SELECT count(*) FROM evidence WHERE user_id = $1", user_id)
        assert count == 1
    finally:
        await _execute("DELETE FROM users WHERE id = $1", user_id)


def test_writes_are_no_ops_when_no_database_configured():
    """Sanity check on the resilience contract every app/db/* function
    documents: with no DATABASE_URL, writes silently no-op rather than
    raising. Doesn't touch the real database itself, but still lives under
    this module's skipif since pytestmark applies file-wide."""

    async def _run():
        assert db_pool.is_available() is False
        await save_job(uuid4(), "raw", ParsedJob(title="x", required_skills=[]))

    asyncio.run(_run())
