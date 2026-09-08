from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.schemas.challenge import Challenge
from app.schemas.evaluation import DEFAULT_RUBRIC_WEIGHTS, SubmissionEvaluationResponse, SubmissionRecord
from app.services.timeline_engine import compute_timeline

USER_ID = uuid4()
NOW = datetime(2026, 6, 1, tzinfo=timezone.utc)


def _challenge(title: str, required_skills: list[str], mutation_reason: str | None = None) -> Challenge:
    return Challenge(
        id=uuid4(), job_id=uuid4(), parent_challenge_id=None,
        title=title, role="Junior Data Analyst",
        scenario="...", instructions="...", required_skills=required_skills, difficulty=1,
        dataset={"tables": []}, expected_output="...",
        evaluation_criteria=DEFAULT_RUBRIC_WEIGHTS, mutation_reason=mutation_reason,
    )


def _evaluation(overall_score: float, evaluated_at: datetime) -> SubmissionEvaluationResponse:
    return SubmissionEvaluationResponse(
        submission_id=uuid4(), evaluation_id=uuid4(),
        rubric_scores={"correctness": 80, "technical_logic": 80, "reasoning": 80, "edge_cases": 80, "efficiency": 80},
        overall_score=overall_score, strengths=[], weaknesses=[], evidence=[], skill_gaps=[],
        sql_execution_result=None, demo_fallback=False, evaluated_at=evaluated_at,
    )


def test_no_submission_history_returns_no_skills():
    response = compute_timeline(USER_ID, submission_history=[])
    assert response.skills == []


def test_single_attempt_produces_one_entry_per_required_skill():
    challenge = _challenge("Revenue Discrepancy", ["SQL", "Problem Solving"])
    evaluation = _evaluation(75.25, NOW)
    response = compute_timeline(USER_ID, [SubmissionRecord(challenge=challenge, evaluation=evaluation)])

    assert {s.skill for s in response.skills} == {"SQL", "Problem Solving"}
    for skill_timeline in response.skills:
        assert len(skill_timeline.entries) == 1
        assert skill_timeline.entries[0].score == 75.25
        assert skill_timeline.entries[0].challenge_title == "Revenue Discrepancy"
        assert skill_timeline.entries[0].mutation_reason is None


def test_mutation_adds_a_second_entry_and_carries_the_mutation_reason():
    original = _challenge("Revenue Discrepancy", ["SQL"])
    mutated = _challenge("Is the Increase Real?", ["Statistics", "SQL"], mutation_reason="targeted weak stats")

    history = [
        SubmissionRecord(challenge=original, evaluation=_evaluation(75.25, NOW)),
        SubmissionRecord(challenge=mutated, evaluation=_evaluation(83.75, NOW + timedelta(days=1))),
    ]
    response = compute_timeline(USER_ID, history)

    sql_timeline = next(s for s in response.skills if s.skill == "SQL")
    assert [e.score for e in sql_timeline.entries] == [75.25, 83.75]
    assert sql_timeline.entries[0].mutation_reason is None
    assert sql_timeline.entries[1].mutation_reason == "targeted weak stats"

    statistics_timeline = next(s for s in response.skills if s.skill == "Statistics")
    assert len(statistics_timeline.entries) == 1
    assert statistics_timeline.entries[0].score == 83.75


def test_entries_stay_in_submission_history_order():
    # submission_history is documented as oldest-first (Section D) — the
    # engine must not re-sort or reverse it.
    challenge = _challenge("Some Challenge", ["SQL"])
    history = [
        SubmissionRecord(challenge=challenge, evaluation=_evaluation(50.0, NOW)),
        SubmissionRecord(challenge=challenge, evaluation=_evaluation(90.0, NOW - timedelta(days=10))),
    ]
    response = compute_timeline(USER_ID, history)
    sql_timeline = response.skills[0]
    assert [e.score for e in sql_timeline.entries] == [50.0, 90.0]


def test_skill_names_are_normalized_and_merged_across_challenges():
    # "Postgres" and "SQL" should merge into one timeline via skill_engine's
    # alias map, same as every other engine in this codebase.
    challenge_a = _challenge("Challenge A", ["Postgres"])
    challenge_b = _challenge("Challenge B", ["SQL"])
    history = [
        SubmissionRecord(challenge=challenge_a, evaluation=_evaluation(60.0, NOW)),
        SubmissionRecord(challenge=challenge_b, evaluation=_evaluation(70.0, NOW + timedelta(days=1))),
    ]
    response = compute_timeline(USER_ID, history)

    assert len(response.skills) == 1
    assert response.skills[0].skill == "SQL"
    assert [e.score for e in response.skills[0].entries] == [60.0, 70.0]


def test_skill_outside_the_taxonomy_keeps_its_original_casing():
    # normalize_skill only trims-and-returns an unrecognized skill rather
    # than restoring casing from a lowercased key — the engine must derive
    # the display name once per skill, not by re-deriving it from its
    # lowercase dict key (which would have lost the casing).
    challenge = _challenge("Some Challenge", ["Excel VBA Macros"])
    history = [SubmissionRecord(challenge=challenge, evaluation=_evaluation(60.0, NOW))]
    response = compute_timeline(USER_ID, history)
    assert response.skills[0].skill == "Excel VBA Macros"
