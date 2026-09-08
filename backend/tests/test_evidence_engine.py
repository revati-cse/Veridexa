from uuid import uuid4

from app.schemas.challenge import Challenge
from app.schemas.evaluation import (
    DEFAULT_RUBRIC_WEIGHTS,
    EvidenceObservation,
    SkillGapItem,
    SubmissionEvaluationResponse,
    SubmissionRecord,
)
from app.schemas.github import ClaimVsEvidenceItem, GithubAnalyzeResponse, LanguageDetected, SkillEvidenceItem
from app.schemas.project import ProjectDescriptionAnalyzeResponse
from app.services.evidence_engine import compute_evidence

USER_ID = uuid4()

GITHUB_EVIDENCE = GithubAnalyzeResponse(
    repository_id=uuid4(),
    repository="https://github.com/example/repo",
    languages_detected=[LanguageDetected(language="Python", confidence=0.9)],
    skills=[
        SkillEvidenceItem(
            skill="Python", evidence_strength="strong", confidence=0.9,
            observations=["Pandas used for data cleaning", "API implementation with tests"],
        ),
        SkillEvidenceItem(skill="SQL", evidence_strength="none", confidence=0.0, observations=[]),
    ],
    claims_vs_evidence=[
        ClaimVsEvidenceItem(skill="Python", claim="advanced", repository_evidence="strong", assessment="x"),
    ],
)

PROJECT_DESCRIPTION_EVIDENCE = ProjectDescriptionAnalyzeResponse(
    source_id=uuid4(),
    skills=[
        SkillEvidenceItem(
            skill="Power BI", evidence_strength="moderate", confidence=0.5,
            observations=["Built a monthly revenue dashboard by customer"],
        ),
    ],
    claims_vs_evidence=[],
)


def _submission_record(skill: str, observation: str) -> SubmissionRecord:
    challenge = Challenge(
        id=uuid4(), job_id=uuid4(), parent_challenge_id=None,
        title="Investigate the Revenue Discrepancy", role="Junior Data Analyst",
        scenario="...", instructions="...", required_skills=[skill], difficulty=1,
        dataset={"tables": []}, expected_output="...",
        evaluation_criteria=DEFAULT_RUBRIC_WEIGHTS, mutation_reason=None,
    )
    evaluation = SubmissionEvaluationResponse(
        submission_id=uuid4(), evaluation_id=uuid4(),
        rubric_scores={"correctness": 85, "technical_logic": 80, "reasoning": 70, "edge_cases": 55, "efficiency": 75},
        overall_score=75.25, strengths=[], weaknesses=[],
        evidence=[EvidenceObservation(skill=skill, observation=observation, confidence=0.85)],
        skill_gaps=[SkillGapItem(skill="Statistics", missing_concepts=["Hypothesis testing"])],
        sql_execution_result=None, demo_fallback=False,
    )
    return SubmissionRecord(challenge=challenge, evaluation=evaluation)


def test_compute_evidence_with_no_sources_returns_empty():
    response = compute_evidence(USER_ID, github_evidence=None, submission_history=[])

    assert response.user_id == USER_ID
    assert response.skills == []


def test_compute_evidence_builds_one_row_per_github_observation():
    response = compute_evidence(USER_ID, github_evidence=GITHUB_EVIDENCE, submission_history=[])

    python_group = next(g for g in response.skills if g.skill == "Python")
    assert len(python_group.evidence) == 2
    assert all(item.source_type == "github" for item in python_group.evidence)
    assert all(item.source_reference == "https://github.com/example/repo" for item in python_group.evidence)
    assert all(item.confidence == 0.9 for item in python_group.evidence)


def test_compute_evidence_skill_with_no_observations_produces_no_rows():
    # SQL has evidence_strength "none" and an empty observations list — no
    # row should be fabricated just because the skill was assessed.
    response = compute_evidence(USER_ID, github_evidence=GITHUB_EVIDENCE, submission_history=[])

    assert not any(g.skill == "SQL" for g in response.skills)


def test_compute_evidence_builds_rows_from_submission_history():
    record = _submission_record("SQL", "Correct JOIN and GROUP BY usage")
    response = compute_evidence(USER_ID, github_evidence=None, submission_history=[record])

    sql_group = next(g for g in response.skills if g.skill == "SQL")
    assert len(sql_group.evidence) == 1
    assert sql_group.evidence[0].source_type == "submission"
    assert sql_group.evidence[0].source_reference == "Investigate the Revenue Discrepancy"
    assert sql_group.evidence[0].observation == "Correct JOIN and GROUP BY usage"


def test_compute_evidence_combines_and_groups_both_sources_by_skill():
    record = _submission_record("Python", "Correct use of pandas groupby")
    response = compute_evidence(USER_ID, github_evidence=GITHUB_EVIDENCE, submission_history=[record])

    python_group = next(g for g in response.skills if g.skill == "Python")
    assert len(python_group.evidence) == 3  # 2 from github + 1 from the submission
    sources = {item.source_type for item in python_group.evidence}
    assert sources == {"github", "submission"}


def test_compute_evidence_builds_one_row_per_project_description_observation():
    response = compute_evidence(
        USER_ID, github_evidence=None, submission_history=[],
        project_description_evidence=PROJECT_DESCRIPTION_EVIDENCE,
    )

    powerbi_group = next(g for g in response.skills if g.skill == "Power BI")
    assert len(powerbi_group.evidence) == 1
    assert powerbi_group.evidence[0].source_type == "project"
    assert powerbi_group.evidence[0].source_reference == "Project description"
    assert powerbi_group.evidence[0].confidence == 0.5


def test_compute_evidence_combines_github_and_project_description_sources():
    response = compute_evidence(
        USER_ID, github_evidence=GITHUB_EVIDENCE, submission_history=[],
        project_description_evidence=PROJECT_DESCRIPTION_EVIDENCE,
    )

    skills_present = {g.skill for g in response.skills}
    assert "Python" in skills_present  # from GitHub
    assert "Power BI" in skills_present  # from the project description


def test_compute_evidence_never_produces_a_row_from_a_claim():
    # compute_evidence() takes no `claims` parameter at all — this asserts
    # the function signature itself, since a claim should be structurally
    # impossible to leak into an evidence row (Section 2: claim != evidence).
    import inspect

    assert "claims" not in inspect.signature(compute_evidence).parameters
