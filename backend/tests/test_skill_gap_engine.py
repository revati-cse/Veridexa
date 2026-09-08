from uuid import uuid4

from app.schemas.challenge import Challenge
from app.schemas.evaluation import (
    DEFAULT_RUBRIC_WEIGHTS,
    SkillGapItem,
    SubmissionEvaluationResponse,
    SubmissionRecord,
)
from app.schemas.readiness import SkillScoreBreakdown
from app.services.skill_gap_engine import GAP_SCORE_THRESHOLD, compute_skill_gaps


def _row(skill: str, importance: str, score: float) -> SkillScoreBreakdown:
    weight = {"high": 3, "medium": 2, "low": 1}[importance]
    return SkillScoreBreakdown(
        skill=skill, importance=importance, importance_weight=weight,
        score=score, weighted_contribution=round(score * weight, 2),
    )


def _record_with_gap(skill: str, missing_concepts: list[str]) -> SubmissionRecord:
    challenge = Challenge(
        id=uuid4(), job_id=uuid4(), parent_challenge_id=None,
        title="Some Challenge", role="Junior Data Analyst",
        scenario="...", instructions="...", required_skills=[skill], difficulty=1,
        dataset={"tables": []}, expected_output="...",
        evaluation_criteria=DEFAULT_RUBRIC_WEIGHTS, mutation_reason=None,
    )
    evaluation = SubmissionEvaluationResponse(
        submission_id=uuid4(), evaluation_id=uuid4(),
        rubric_scores={"correctness": 60, "technical_logic": 60, "reasoning": 60, "edge_cases": 60, "efficiency": 60},
        overall_score=60.0, strengths=[], weaknesses=[],
        evidence=[], skill_gaps=[SkillGapItem(skill=skill, missing_concepts=missing_concepts)],
        sql_execution_result=None, demo_fallback=False,
    )
    return SubmissionRecord(challenge=challenge, evaluation=evaluation)


def test_skill_above_threshold_is_excluded():
    rows = [_row("SQL", "high", 80.0)]
    assert compute_skill_gaps(rows, []) == []


def test_skill_below_threshold_is_included_with_matching_missing_concepts():
    rows = [_row("Statistics", "medium", 61.0)]
    history = [_record_with_gap("Statistics", ["Hypothesis testing", "Statistical significance"])]

    gaps = compute_skill_gaps(rows, history)

    assert len(gaps) == 1
    assert gaps[0].skill == "Statistics"
    assert gaps[0].missing_concepts == ["Hypothesis testing", "Statistical significance"]


def test_skill_below_threshold_with_no_history_still_included_with_empty_concepts():
    # An unassessed required skill (score 0, no submissions at all) is still
    # a real gap worth surfacing — just without concrete concepts to point to.
    rows = [_row("Python", "high", 0.0)]

    gaps = compute_skill_gaps(rows, [])

    assert gaps == [SkillGapItem(skill="Python", missing_concepts=[])]


def test_score_exactly_at_threshold_is_not_a_gap():
    rows = [_row("SQL", "high", GAP_SCORE_THRESHOLD)]
    assert compute_skill_gaps(rows, []) == []


def test_sorted_by_importance_first_then_lowest_score():
    rows = [
        _row("A", "low", 10.0),
        _row("B", "high", 65.0),
        _row("C", "high", 40.0),
        _row("D", "medium", 20.0),
    ]

    gaps = compute_skill_gaps(rows, [])

    assert [g.skill for g in gaps] == ["C", "B", "D", "A"]


def test_uses_most_recent_submissions_gap_for_a_skill_not_the_first():
    rows = [_row("Statistics", "medium", 61.0)]
    older = _record_with_gap("Statistics", ["Old concept"])
    newer = _record_with_gap("Statistics", ["Newer, more specific concept"])

    gaps = compute_skill_gaps(rows, [older, newer])

    assert gaps[0].missing_concepts == ["Newer, more specific concept"]


def test_empty_breakdown_returns_empty():
    assert compute_skill_gaps([], []) == []
