import asyncio
from unittest.mock import AsyncMock, patch

from app.ai.claude_client import AIServiceUnavailable
from app.schemas.github import GithubAnalysisAIOutput, SkillEvidenceItem
from app.schemas.skill import ClaimedSkill
from app.services.project_description_analyzer import analyze_description


def test_successful_claude_call_returns_its_skills_not_the_fixture():
    ai_output = GithubAnalysisAIOutput(
        skills=[SkillEvidenceItem(skill="Python", evidence_strength="moderate", confidence=0.5, observations=["x"])]
    )
    with patch("app.services.project_description_analyzer.call_structured", new=AsyncMock(return_value=ai_output)):
        skills, claims_vs_evidence, used_fallback = asyncio.run(
            analyze_description("A description of a project.", claimed_skills=[], required_skills=["Python"])
        )

    assert used_fallback is False
    assert skills[0].skill == "Python"


def test_claude_failure_falls_back_to_fixture():
    with patch(
        "app.services.project_description_analyzer.call_structured",
        new=AsyncMock(side_effect=AIServiceUnavailable("no key configured")),
    ):
        skills, claims_vs_evidence, used_fallback = asyncio.run(
            analyze_description("A description of a project.", claimed_skills=[], required_skills=[])
        )

    assert used_fallback is True
    assert len(skills) > 0  # demo_project_description_evidence.json fixture loaded


def test_claims_vs_evidence_uses_description_specific_wording_not_repository_wording():
    ai_output = GithubAnalysisAIOutput(
        skills=[SkillEvidenceItem(skill="SQL", evidence_strength="strong", confidence=0.9, observations=["x"])]
    )
    with patch("app.services.project_description_analyzer.call_structured", new=AsyncMock(return_value=ai_output)):
        skills, claims_vs_evidence, used_fallback = asyncio.run(
            analyze_description(
                "A description of a project.",
                claimed_skills=[ClaimedSkill(skill="SQL", level="advanced")],
                required_skills=[],
            )
        )

    assert "description" in claims_vs_evidence[0].assessment.lower()
    assert "repository" not in claims_vs_evidence[0].assessment.lower()
