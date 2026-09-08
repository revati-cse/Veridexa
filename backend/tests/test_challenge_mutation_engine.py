import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.ai.claude_client import AIServiceUnavailable
from app.schemas.challenge import Challenge, MutatedChallengeAIOutput
from app.schemas.evaluation import (
    DEFAULT_RUBRIC_WEIGHTS,
    SkillGapItem,
    SubmissionEvaluationResponse,
    SubmissionRecord,
)
from app.schemas.sandbox import SandboxDataset, SandboxTable
from app.services.challenge_mutation_engine import adapt_difficulty, mutate_challenge


def _previous_attempt(overall_score: float, skill_gaps: list[SkillGapItem], difficulty=1) -> SubmissionRecord:
    challenge = Challenge(
        id=uuid4(), job_id=uuid4(), parent_challenge_id=None,
        title="Investigate the Revenue Discrepancy", role="Junior Data Analyst",
        scenario="Revenue looks inflated.", instructions="...",
        required_skills=["SQL", "Statistics"], difficulty=difficulty,
        dataset={"tables": []}, expected_output="...",
        evaluation_criteria=DEFAULT_RUBRIC_WEIGHTS, mutation_reason=None,
    )
    evaluation = SubmissionEvaluationResponse(
        submission_id=uuid4(), evaluation_id=uuid4(),
        rubric_scores={"correctness": 70, "technical_logic": 70, "reasoning": 70, "edge_cases": 55, "efficiency": 70},
        overall_score=overall_score,
        strengths=["Correct JOIN"],
        weaknesses=["Did not address statistical significance"],
        evidence=[], skill_gaps=skill_gaps, sql_execution_result=None, demo_fallback=False,
    )
    return SubmissionRecord(challenge=challenge, evaluation=evaluation)


AI_OUTPUT = MutatedChallengeAIOutput(
    title="Is the Increase Statistically Significant?",
    role="Junior Data Analyst",
    scenario="A different, statistics-focused scenario.",
    instructions="Determine whether the increase is statistically significant.",
    required_skills=["Statistics", "SQL"],
    dataset=SandboxDataset(
        tables=[SandboxTable(name="monthly_orders", columns=["id", "amount"], rows=[[1, 100], [2, 120]])]
    ),
    expected_output="A significance conclusion with reasoning.",
    mutation_reason="Targeted because your previous submission didn't address statistical significance.",
)


def test_adapt_difficulty_increases_on_high_score_capped_at_max():
    assert adapt_difficulty(90.0, 1) == 2
    assert adapt_difficulty(85.0, 1) == 2  # boundary: >= 85 counts as high
    assert adapt_difficulty(90.0, 3) == 3  # capped, doesn't overflow


def test_adapt_difficulty_decreases_on_low_score_capped_at_min():
    assert adapt_difficulty(40.0, 2) == 1
    assert adapt_difficulty(59.9, 2) == 1
    assert adapt_difficulty(40.0, 1) == 1  # capped, doesn't underflow


def test_adapt_difficulty_unchanged_in_the_middle_band():
    assert adapt_difficulty(60.0, 2) == 2  # boundary: exactly 60 is NOT "low"
    assert adapt_difficulty(75.0, 2) == 2
    assert adapt_difficulty(84.9, 2) == 2


def test_mutate_challenge_uses_claude_output_with_backend_assigned_difficulty():
    attempt = _previous_attempt(
        overall_score=61.0,
        skill_gaps=[SkillGapItem(skill="Statistics", missing_concepts=["Hypothesis testing"])],
        difficulty=1,
    )
    job_id = uuid4()

    with patch("app.services.challenge_mutation_engine.call_structured", new=AsyncMock(return_value=AI_OUTPUT)):
        challenge, used_fallback = asyncio.run(
            mutate_challenge(job_id=job_id, job_title="Data Analyst", required_skills=["SQL", "Statistics"], previous_attempt=attempt)
        )

    assert used_fallback is False
    assert challenge.job_id == job_id
    assert challenge.parent_challenge_id == attempt.challenge.id
    assert challenge.title == AI_OUTPUT.title
    assert challenge.mutation_reason == AI_OUTPUT.mutation_reason
    # 61.0 < 60 is False (not low), so difficulty stays at 1 — backend-computed, not from AI output.
    assert challenge.difficulty == 1
    assert challenge.evaluation_criteria == DEFAULT_RUBRIC_WEIGHTS


def test_mutate_challenge_difficulty_actually_adapts_from_previous_score():
    attempt = _previous_attempt(overall_score=90.0, skill_gaps=[], difficulty=1)

    with patch("app.services.challenge_mutation_engine.call_structured", new=AsyncMock(return_value=AI_OUTPUT)):
        challenge, _ = asyncio.run(
            mutate_challenge(job_id=uuid4(), job_title="Data Analyst", required_skills=["SQL"], previous_attempt=attempt)
        )

    assert challenge.difficulty == 2  # stepped up from a 90.0 score


def test_mutate_challenge_falls_back_to_fixture_when_claude_unavailable():
    attempt = _previous_attempt(
        overall_score=61.0,
        skill_gaps=[SkillGapItem(skill="Statistics", missing_concepts=["Hypothesis testing"])],
    )

    with patch(
        "app.services.challenge_mutation_engine.call_structured",
        new=AsyncMock(side_effect=AIServiceUnavailable("no API key configured")),
    ):
        challenge, used_fallback = asyncio.run(
            mutate_challenge(job_id=uuid4(), job_title="Data Analyst", required_skills=["Statistics"], previous_attempt=attempt)
        )

    assert used_fallback is True
    assert challenge.title  # fixture content is non-empty
    assert challenge.mutation_reason  # fixture carries its own reason
    assert challenge.parent_challenge_id == attempt.challenge.id
    assert challenge.difficulty == 1  # still backend-computed on the fallback path (61 is not < 60)


def test_fixture_dataset_is_actually_runnable_in_the_sql_sandbox():
    from app.sandbox.sql_runner import run_sql
    from app.services.challenge_mutation_engine import _load_fixture

    fixture = _load_fixture()
    result = run_sql("SELECT month, AVG(amount) FROM monthly_orders GROUP BY month", fixture.dataset.model_dump())

    assert result.success is True
    assert result.row_count == 2  # two distinct months in the fixture


def test_mutation_targets_the_evaluations_own_first_skill_gap_not_a_fresh_computation():
    # skill_gaps[0] is what Section P's own pseudocode reuses directly — this
    # asserts the prompt actually receives it, via the built prompt text.
    from app.ai.prompts.mutation_prompt import build_user_prompt

    prompt = build_user_prompt(
        previous_scenario="...", previous_required_skills=["SQL"],
        weaknesses=["Missed NULLs"], target_skill="Statistics",
        missing_concepts=["Hypothesis testing"], job_title="Data Analyst",
        required_skills=["Statistics"], difficulty=2,
    )

    assert "Specifically target this skill gap: Statistics" in prompt
    assert "Hypothesis testing" in prompt


def test_mutation_prompt_handles_no_identified_skill_gap():
    from app.ai.prompts.mutation_prompt import build_user_prompt

    prompt = build_user_prompt(
        previous_scenario="...", previous_required_skills=["SQL"],
        weaknesses=["Missed edge cases"], target_skill=None,
        missing_concepts=[], job_title="Data Analyst",
        required_skills=["SQL"], difficulty=1,
    )

    assert "No specific skill gap was identified" in prompt
