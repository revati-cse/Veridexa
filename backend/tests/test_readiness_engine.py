from uuid import uuid4

from app.schemas.challenge import Challenge
from app.schemas.evaluation import (
    DEFAULT_RUBRIC_WEIGHTS,
    SkillGapItem,
    SubmissionEvaluationResponse,
    SubmissionRecord,
)
from app.schemas.github import ClaimVsEvidenceItem, GithubAnalyzeResponse, LanguageDetected, SkillEvidenceItem
from app.schemas.job import JobRequiredSkill
from app.schemas.skill import ClaimedSkill
from app.services.readiness_engine import compute_readiness

USER_ID = uuid4()
JOB_ID = uuid4()


def _challenge(required_skills: list[str]) -> Challenge:
    return Challenge(
        id=uuid4(), job_id=JOB_ID, parent_challenge_id=None,
        title="Some Challenge", role="Junior Data Analyst",
        scenario="...", instructions="...", required_skills=required_skills, difficulty=1,
        dataset={"tables": []}, expected_output="...",
        evaluation_criteria=DEFAULT_RUBRIC_WEIGHTS, mutation_reason=None,
    )


def _evaluation(overall_score: float, skill_gaps: list[SkillGapItem] | None = None) -> SubmissionEvaluationResponse:
    return SubmissionEvaluationResponse(
        submission_id=uuid4(), evaluation_id=uuid4(),
        rubric_scores={"correctness": 80, "technical_logic": 80, "reasoning": 80, "edge_cases": 80, "efficiency": 80},
        overall_score=overall_score, strengths=[], weaknesses=[], evidence=[],
        skill_gaps=skill_gaps or [], sql_execution_result=None, demo_fallback=False,
    )


def _github(skill: str, strength: str) -> GithubAnalyzeResponse:
    return GithubAnalyzeResponse(
        repository_id=uuid4(), repository="https://github.com/example/repo",
        languages_detected=[LanguageDetected(language="Python", confidence=0.9)],
        skills=[SkillEvidenceItem(skill=skill, evidence_strength=strength, confidence=0.8, observations=["x"])],
        claims_vs_evidence=[ClaimVsEvidenceItem(skill=skill, claim=None, repository_evidence=strength, assessment="x")],
    )


def test_skill_with_no_evidence_and_no_claim_scores_zero():
    response = compute_readiness(
        USER_ID, JOB_ID, "Data Analyst",
        required_skills=[JobRequiredSkill(skill="SQL", importance="high")],
        claims=[], github_evidence=None, submission_history=[],
    )

    assert response.skill_breakdown[0].score == 0.0
    assert response.readiness_score == 0.0


def test_skill_with_only_challenge_evidence_normalizes_to_full_weight():
    record = SubmissionRecord(challenge=_challenge(["SQL"]), evaluation=_evaluation(80.0))
    response = compute_readiness(
        USER_ID, JOB_ID, "Data Analyst",
        required_skills=[JobRequiredSkill(skill="SQL", importance="high")],
        claims=[], github_evidence=None, submission_history=[record],
    )

    # Only component present is challenge evidence (weight 0.6) — normalized,
    # it should contribute its full value, not be capped at 0.6 * 80 = 48.
    assert response.skill_breakdown[0].score == 80.0


def test_skill_with_only_github_evidence_normalizes_to_full_weight():
    response = compute_readiness(
        USER_ID, JOB_ID, "Data Analyst",
        required_skills=[JobRequiredSkill(skill="Python", importance="high")],
        claims=[], github_evidence=_github("Python", "strong"), submission_history=[],
    )

    assert response.skill_breakdown[0].score == 90.0  # strong -> 90, normalized to 100% weight


def test_skill_with_challenge_and_github_and_claim_blends_all_three():
    record = SubmissionRecord(challenge=_challenge(["SQL"]), evaluation=_evaluation(80.0))
    response = compute_readiness(
        USER_ID, JOB_ID, "Data Analyst",
        required_skills=[JobRequiredSkill(skill="SQL", importance="high")],
        claims=[ClaimedSkill(skill="SQL", level="advanced")],
        github_evidence=_github("SQL", "moderate"),
        submission_history=[record],
    )

    # challenge=80 (0.6) + github=65 (0.3) + claim=100 corroborated (0.1, since
    # challenge score 80 >= corroboration threshold) = 48 + 19.5 + 10 = 77.5
    assert response.skill_breakdown[0].score == 77.5


def test_claimed_skill_with_no_corroborating_evidence_gets_small_uncorroborated_bonus():
    response = compute_readiness(
        USER_ID, JOB_ID, "Data Analyst",
        required_skills=[JobRequiredSkill(skill="Statistics", importance="medium")],
        claims=[ClaimedSkill(skill="Statistics", level="advanced")],
        github_evidence=None, submission_history=[],
    )

    # claim_bonus alone (50, uncorroborated) is the only component — normalizes to itself.
    assert response.skill_breakdown[0].score == 50.0


def test_multiple_submissions_for_same_skill_use_the_latest_not_an_average():
    older = SubmissionRecord(challenge=_challenge(["Statistics"]), evaluation=_evaluation(61.0))
    newer = SubmissionRecord(challenge=_challenge(["Statistics"]), evaluation=_evaluation(84.0))
    response = compute_readiness(
        USER_ID, JOB_ID, "Data Analyst",
        required_skills=[JobRequiredSkill(skill="Statistics", importance="medium")],
        claims=[], github_evidence=None, submission_history=[older, newer],
    )

    assert response.skill_breakdown[0].score == 84.0  # not (61+84)/2


def test_readiness_score_matches_weighted_formula_exactly():
    high = SubmissionRecord(challenge=_challenge(["SQL"]), evaluation=_evaluation(90.0))
    low = SubmissionRecord(challenge=_challenge(["Statistics"]), evaluation=_evaluation(50.0))
    response = compute_readiness(
        USER_ID, JOB_ID, "Data Analyst",
        required_skills=[
            JobRequiredSkill(skill="SQL", importance="high"),      # weight 3
            JobRequiredSkill(skill="Statistics", importance="medium"),  # weight 2
        ],
        claims=[], github_evidence=None, submission_history=[high, low],
    )

    expected = round((90.0 * 3 + 50.0 * 2) / (3 + 2), 1)
    assert response.readiness_score == expected


def test_readiness_score_is_zero_with_no_required_skills():
    response = compute_readiness(
        USER_ID, JOB_ID, "Data Analyst",
        required_skills=[], claims=[], github_evidence=None, submission_history=[],
    )

    assert response.readiness_score == 0.0
    assert response.skill_breakdown == []


def test_strengths_and_weaknesses_are_derived_from_score_thresholds():
    strong = SubmissionRecord(challenge=_challenge(["SQL"]), evaluation=_evaluation(90.0))
    weak = SubmissionRecord(challenge=_challenge(["Statistics"]), evaluation=_evaluation(40.0))
    response = compute_readiness(
        USER_ID, JOB_ID, "Data Analyst",
        required_skills=[
            JobRequiredSkill(skill="SQL", importance="high"),
            JobRequiredSkill(skill="Statistics", importance="medium"),
        ],
        claims=[], github_evidence=None, submission_history=[strong, weak],
    )

    assert response.strengths == ["SQL"]
    assert response.weaknesses == ["Statistics"]


def test_skill_gaps_come_from_the_most_recent_submissions_evaluation():
    gaps = [SkillGapItem(skill="Statistics", missing_concepts=["Hypothesis testing"])]
    record = SubmissionRecord(challenge=_challenge(["Statistics"]), evaluation=_evaluation(61.0, skill_gaps=gaps))
    response = compute_readiness(
        USER_ID, JOB_ID, "Data Analyst",
        required_skills=[JobRequiredSkill(skill="Statistics", importance="medium")],
        claims=[], github_evidence=None, submission_history=[record],
    )

    assert response.skill_gaps == gaps


def test_skill_normalization_matches_aliased_names_across_sources():
    # Claim uses "MySQL", github evidence uses "PostgreSQL", challenge uses
    # "SQL" — all three must resolve to the same canonical skill.
    record = SubmissionRecord(challenge=_challenge(["SQL"]), evaluation=_evaluation(80.0))
    response = compute_readiness(
        USER_ID, JOB_ID, "Data Analyst",
        required_skills=[JobRequiredSkill(skill="MySQL", importance="high")],
        claims=[ClaimedSkill(skill="MySQL", level="advanced")],
        github_evidence=_github("PostgreSQL", "strong"),
        submission_history=[record],
    )

    assert len(response.skill_breakdown) == 1
    assert response.skill_breakdown[0].skill == "SQL"
