import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.ai.claude_client import AIServiceUnavailable
from app.schemas.challenge import Challenge
from app.schemas.evaluation import DEFAULT_RUBRIC_WEIGHTS, EvaluationResult, EvidenceObservation, RubricScores, SkillGapItem
from app.services.evaluation_engine import evaluate_submission

CHALLENGE = Challenge(
    id=uuid4(),
    job_id=uuid4(),
    parent_challenge_id=None,
    title="Investigate the Revenue Discrepancy",
    role="Junior Data Analyst",
    scenario="Revenue looks inflated.",
    instructions="Write a query that computes corrected revenue per customer.",
    required_skills=["SQL"],
    difficulty=1,
    dataset={
        "tables": [
            {"name": "customers", "columns": ["id", "name"], "rows": [[1, "Alice"], [2, "Bob"]]},
            {"name": "orders", "columns": ["id", "customer_id", "amount"], "rows": [[1, 1, 100], [2, 2, 50]]},
        ]
    },
    expected_output="Corrected revenue per customer.",
    evaluation_criteria=DEFAULT_RUBRIC_WEIGHTS,
    mutation_reason=None,
)

AI_RESULT = EvaluationResult(
    rubric_scores=RubricScores(correctness=90, technical_logic=80, reasoning=70, edge_cases=60, efficiency=100),
    strengths=["Correct JOIN"],
    weaknesses=["Minor style issue"],
    evidence=[EvidenceObservation(skill="SQL", observation="Correct JOIN and GROUP BY", confidence=0.9)],
    skill_gaps=[SkillGapItem(skill="Statistics", missing_concepts=["Hypothesis testing"])],
)


def test_evaluate_submission_runs_sandbox_for_real_and_computes_weighted_score():
    query = "SELECT c.name, o.amount FROM customers c JOIN orders o ON o.customer_id = c.id"

    with patch("app.services.evaluation_engine.call_structured", new=AsyncMock(return_value=AI_RESULT)):
        response, used_fallback = asyncio.run(evaluate_submission(CHALLENGE, query, "I joined the two tables."))

    assert used_fallback is False
    assert response.sql_execution_result.success is True
    assert response.sql_execution_result.row_count == 2
    expected_score = round(
        90 * 0.30 + 80 * 0.25 + 70 * 0.20 + 60 * 0.15 + 100 * 0.10, 2
    )
    assert response.overall_score == expected_score
    assert response.rubric_scores["correctness"] == 90
    assert response.strengths == ["Correct JOIN"]


def test_evaluate_submission_sandbox_still_runs_for_real_on_ai_fallback():
    # The sandbox result must reflect the *actual* submitted query even when
    # the AI reasoning pass falls back to the fixture — never faked together.
    bad_query = "SELECT * FROM does_not_exist"

    with patch(
        "app.services.evaluation_engine.call_structured",
        new=AsyncMock(side_effect=AIServiceUnavailable("no API key configured")),
    ):
        response, used_fallback = asyncio.run(evaluate_submission(CHALLENGE, bad_query, "explanation"))

    assert used_fallback is True
    assert response.sql_execution_result.success is False
    assert "no such table" in response.sql_execution_result.error.lower()
    assert response.overall_score > 0  # still computed from the fixture's rubric_scores


def test_evaluate_submission_with_no_code_is_rejected_by_sandbox_but_still_evaluated():
    with patch("app.services.evaluation_engine.call_structured", new=AsyncMock(return_value=AI_RESULT)):
        response, _ = asyncio.run(evaluate_submission(CHALLENGE, "", "I wasn't sure how to approach this."))

    assert response.sql_execution_result.success is False
    assert response.sql_execution_result.rejected_reason == "No SQL was submitted."
    assert response.overall_score > 0  # AI still scores the explanation/reasoning


def test_evaluate_submission_malicious_query_is_rejected_not_executed():
    with patch("app.services.evaluation_engine.call_structured", new=AsyncMock(return_value=AI_RESULT)):
        response, _ = asyncio.run(
            evaluate_submission(CHALLENGE, "DROP TABLE customers", "trying to clean up")
        )

    assert response.sql_execution_result.success is False
    assert response.sql_execution_result.rejected_reason is not None


def test_overall_score_never_returned_by_the_ai_even_if_it_tried():
    # AI_RESULT (EvaluationResult) has no overall_score field at all — it's
    # structurally impossible for the model to set it. This test documents
    # that guarantee rather than re-deriving arithmetic already covered above.
    assert not hasattr(AI_RESULT, "overall_score")


def test_rubric_scores_requires_all_five_canonical_criteria():
    with pytest.raises(ValidationError):
        RubricScores(correctness=90, technical_logic=80, reasoning=70, edge_cases=60)  # missing "efficiency"


def test_rubric_scores_rejects_out_of_range_values():
    with pytest.raises(ValidationError):
        RubricScores(correctness=150, technical_logic=80, reasoning=70, edge_cases=60, efficiency=50)


def test_ai_fallback_uses_the_mutated_fixture_for_a_mutated_challenge():
    # A mutated challenge (parent_challenge_id set) targets a different skill
    # than the original — falling back to the same static demo_evaluation.json
    # fixture for both would show SQL-flavored weaknesses on what's actually a
    # Statistics challenge. The fallback must pick the fixture that matches.
    mutated_challenge = CHALLENGE.model_copy(
        update={"id": uuid4(), "parent_challenge_id": CHALLENGE.id, "required_skills": ["Statistics", "SQL"]}
    )

    with patch(
        "app.services.evaluation_engine.call_structured",
        new=AsyncMock(side_effect=AIServiceUnavailable("no API key configured")),
    ):
        original_response, _ = asyncio.run(evaluate_submission(CHALLENGE, "SELECT 1", "explanation"))
        mutated_response, _ = asyncio.run(evaluate_submission(mutated_challenge, "SELECT 1", "explanation"))

    assert original_response.weaknesses != mutated_response.weaknesses
    assert any("customer_id" in w for w in original_response.weaknesses)
    assert any("statistic" in w.lower() or "p-value" in w.lower() for w in mutated_response.weaknesses)
    assert mutated_response.overall_score > original_response.overall_score
