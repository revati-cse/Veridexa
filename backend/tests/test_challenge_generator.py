import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.ai.claude_client import AIServiceUnavailable
from app.schemas.challenge import ChallengeAIOutput
from app.schemas.evaluation import DEFAULT_RUBRIC_WEIGHTS
from app.schemas.sandbox import SandboxDataset, SandboxTable
from app.services.challenge_generator import generate_challenge

AI_OUTPUT = ChallengeAIOutput(
    title="Diagnose the Checkout Funnel Drop",
    role="Junior Data Analyst",
    scenario="Conversion dropped 15% after a release. You have events and users tables.",
    instructions="Write a SQL query identifying which step of the funnel regressed.",
    required_skills=["SQL", "Problem Solving"],
    dataset=SandboxDataset(
        tables=[
            SandboxTable(name="events", columns=["id", "user_id", "step"], rows=[[1, 1, "view"], [2, 1, "cart"]]),
        ]
    ),
    expected_output="A per-step conversion count with the regressed step identified.",
)


def test_generate_challenge_uses_claude_output_with_backend_assigned_fields():
    job_id = uuid4()
    with patch("app.services.challenge_generator.call_structured", new=AsyncMock(return_value=AI_OUTPUT)):
        challenge, used_fallback = asyncio.run(
            generate_challenge(job_id=job_id, job_title="Data Analyst", required_skills=["SQL"], difficulty=2)
        )

    assert used_fallback is False
    assert challenge.job_id == job_id
    assert challenge.parent_challenge_id is None
    assert challenge.title == AI_OUTPUT.title
    assert challenge.scenario == AI_OUTPUT.scenario
    # Backend-assigned, not LLM-authored:
    assert challenge.difficulty == 2
    assert challenge.evaluation_criteria == DEFAULT_RUBRIC_WEIGHTS
    assert sum(challenge.evaluation_criteria.values()) == 1.0
    # dataset round-trips through model_dump() into a plain dict the sandbox can consume
    assert challenge.dataset["tables"][0]["name"] == "events"


def test_generate_challenge_falls_back_to_fixture_when_claude_unavailable():
    job_id = uuid4()
    with patch(
        "app.services.challenge_generator.call_structured",
        new=AsyncMock(side_effect=AIServiceUnavailable("no API key configured")),
    ):
        challenge, used_fallback = asyncio.run(
            generate_challenge(job_id=job_id, job_title="Data Analyst", required_skills=["SQL"], difficulty=1)
        )

    assert used_fallback is True
    assert challenge.title  # fixture content is non-empty
    assert challenge.difficulty == 1  # still backend-assigned even on the fallback path
    assert challenge.evaluation_criteria == DEFAULT_RUBRIC_WEIGHTS
    assert challenge.dataset["tables"]


def test_fixture_dataset_is_actually_runnable_in_the_sql_sandbox():
    """The demo fixture isn't just schema-valid — it must be a real dataset
    the sandbox can seed and query, since it's what the demo runs on when
    Claude is unavailable."""
    from app.sandbox.sql_runner import run_sql
    from app.services.challenge_generator import _load_fixture

    fixture = _load_fixture()
    result = run_sql(
        "SELECT c.name, SUM(o.amount) AS total FROM customers c JOIN orders o ON o.customer_id = c.id GROUP BY c.name",
        fixture.dataset.model_dump(),
    )

    assert result.success is True
    assert result.row_count > 0
