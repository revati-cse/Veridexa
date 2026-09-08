from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.schemas.challenge import Challenge
from app.schemas.evaluation import DEFAULT_RUBRIC_WEIGHTS, SubmissionEvaluationResponse, SubmissionRecord
from app.schemas.github import ClaimVsEvidenceItem, GithubAnalyzeResponse, LanguageDetected, SkillEvidenceItem
from app.schemas.job import JobRequiredSkill
from app.services.freshness_engine import compute_freshness

USER_ID = uuid4()
NOW = datetime(2026, 6, 1, tzinfo=timezone.utc)


def _challenge(required_skills: list[str]) -> Challenge:
    return Challenge(
        id=uuid4(), job_id=uuid4(), parent_challenge_id=None,
        title="Some Challenge", role="Junior Data Analyst",
        scenario="...", instructions="...", required_skills=required_skills, difficulty=1,
        dataset={"tables": []}, expected_output="...",
        evaluation_criteria=DEFAULT_RUBRIC_WEIGHTS, mutation_reason=None,
    )


def _evaluation(evaluated_at: datetime) -> SubmissionEvaluationResponse:
    return SubmissionEvaluationResponse(
        submission_id=uuid4(), evaluation_id=uuid4(),
        rubric_scores={"correctness": 80, "technical_logic": 80, "reasoning": 80, "edge_cases": 80, "efficiency": 80},
        overall_score=80, strengths=[], weaknesses=[], evidence=[], skill_gaps=[],
        sql_execution_result=None, demo_fallback=False, evaluated_at=evaluated_at,
    )


def _github(skill: str, strength: str, analyzed_at: datetime) -> GithubAnalyzeResponse:
    return GithubAnalyzeResponse(
        repository_id=uuid4(), repository="https://github.com/example/repo",
        languages_detected=[LanguageDetected(language="Python", confidence=0.9)],
        skills=[SkillEvidenceItem(skill=skill, evidence_strength=strength, confidence=0.8, observations=["x"])],
        claims_vs_evidence=[ClaimVsEvidenceItem(skill=skill, claim=None, repository_evidence=strength, assessment="x")],
        analyzed_at=analyzed_at,
    )


def test_skill_with_no_evidence_at_all_is_not_assessed():
    response = compute_freshness(
        USER_ID, required_skills=[JobRequiredSkill(skill="SQL", importance="high")],
        github_evidence=None, submission_history=[], now=NOW,
    )
    row = response.skills[0]
    assert row.freshness == "not_assessed"
    assert row.last_evidence_at is None
    assert row.days_since_last_evidence is None


def test_recent_submission_is_fresh():
    challenge = _challenge(["SQL"])
    evaluation = _evaluation(evaluated_at=NOW - timedelta(days=5))
    response = compute_freshness(
        USER_ID, required_skills=[JobRequiredSkill(skill="SQL", importance="high")],
        github_evidence=None,
        submission_history=[SubmissionRecord(challenge=challenge, evaluation=evaluation)],
        now=NOW,
    )
    row = response.skills[0]
    assert row.freshness == "fresh"
    assert row.days_since_last_evidence == 5


def test_old_github_evidence_is_stale():
    github_evidence = _github("Python", "strong", analyzed_at=NOW - timedelta(days=400))
    response = compute_freshness(
        USER_ID, required_skills=[JobRequiredSkill(skill="Python", importance="high")],
        github_evidence=github_evidence, submission_history=[], now=NOW,
    )
    row = response.skills[0]
    assert row.freshness == "stale"
    assert row.days_since_last_evidence == 400


def test_evidence_strength_none_does_not_count_as_evidence():
    # evidence_strength="none" means github_analyzer found nothing for this
    # skill — it must not be treated as "assessed 0 days ago" just because
    # the repo itself was analyzed recently.
    github_evidence = _github("Statistics", "none", analyzed_at=NOW - timedelta(days=1))
    response = compute_freshness(
        USER_ID, required_skills=[JobRequiredSkill(skill="Statistics", importance="medium")],
        github_evidence=github_evidence, submission_history=[], now=NOW,
    )
    assert response.skills[0].freshness == "not_assessed"


def test_aging_boundary_is_inclusive_of_30_days_and_exclusive_above():
    challenge = _challenge(["SQL"])

    exactly_30 = compute_freshness(
        USER_ID, required_skills=[JobRequiredSkill(skill="SQL", importance="high")],
        github_evidence=None,
        submission_history=[SubmissionRecord(challenge=challenge, evaluation=_evaluation(NOW - timedelta(days=30)))],
        now=NOW,
    )
    assert exactly_30.skills[0].freshness == "fresh"

    just_over_30 = compute_freshness(
        USER_ID, required_skills=[JobRequiredSkill(skill="SQL", importance="high")],
        github_evidence=None,
        submission_history=[SubmissionRecord(challenge=challenge, evaluation=_evaluation(NOW - timedelta(days=31)))],
        now=NOW,
    )
    assert just_over_30.skills[0].freshness == "aging"


def test_most_recent_evidence_wins_across_github_and_submission_sources():
    # SQL has both a stale GitHub read and a fresh submission — the more
    # recent source should determine freshness, same "latest wins"
    # convention readiness_engine uses for scores.
    challenge = _challenge(["SQL"])
    evaluation = _evaluation(evaluated_at=NOW - timedelta(days=2))
    github_evidence = _github("SQL", "moderate", analyzed_at=NOW - timedelta(days=300))

    response = compute_freshness(
        USER_ID, required_skills=[JobRequiredSkill(skill="SQL", importance="high")],
        github_evidence=github_evidence,
        submission_history=[SubmissionRecord(challenge=challenge, evaluation=evaluation)],
        now=NOW,
    )
    row = response.skills[0]
    assert row.days_since_last_evidence == 2
    assert row.freshness == "fresh"


def test_skill_names_are_normalized_before_matching():
    # "Postgres" in the GitHub evidence should match a required "SQL" skill
    # via skill_engine's alias map, same as every other engine in this codebase.
    github_evidence = _github("Postgres", "strong", analyzed_at=NOW - timedelta(days=10))
    response = compute_freshness(
        USER_ID, required_skills=[JobRequiredSkill(skill="SQL", importance="high")],
        github_evidence=github_evidence, submission_history=[], now=NOW,
    )
    assert response.skills[0].skill == "SQL"
    assert response.skills[0].freshness == "fresh"
