import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.ai.claude_client import AIServiceUnavailable
from app.github.client import GithubAccessError
from app.schemas.github import GithubAnalysisAIOutput, SkillEvidenceItem
from app.schemas.skill import ClaimedSkill
from app.services.github_analyzer import analyze_repository


class FakeGithubClient:
    """Stands in for app.github.client.GithubClient in tests — no network."""

    def __init__(self, metadata=None, languages=None, tree=None, contents=None, fail_with=None):
        self._metadata = metadata or {"default_branch": "main"}
        self._languages = languages or {"Python": 900, "SQL": 100}
        self._tree = tree or [
            {"path": "src/etl.py", "type": "blob", "size": 500},
            {"path": "queries/report.sql", "type": "blob", "size": 300},
            {"path": "requirements.txt", "type": "blob", "size": 50},
        ]
        self._contents = contents or {
            "src/etl.py": "import pandas as pd\n\ndef clean(df):\n    return df.dropna()\n",
            "queries/report.sql": "SELECT customer_id, SUM(amount) FROM orders GROUP BY customer_id;",
            "requirements.txt": "pandas==2.2.0\n",
        }
        self._fail_with = fail_with

    async def __aenter__(self):
        if self._fail_with:
            raise self._fail_with
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def get_metadata(self, ref):
        return self._metadata

    async def get_languages(self, ref):
        return self._languages

    async def get_tree(self, ref, branch):
        return self._tree

    async def get_file_content(self, ref, path):
        return self._contents.get(path)


def _fake_client_factory(**kwargs):
    def factory(*_args, **_kwargs):
        return FakeGithubClient(**kwargs)

    return factory


def test_analyze_repository_success_builds_languages_skills_and_claims():
    ai_output = GithubAnalysisAIOutput(
        skills=[
            SkillEvidenceItem(skill="Python", evidence_strength="strong", confidence=0.9, observations=["pandas usage"]),
            SkillEvidenceItem(skill="SQL", evidence_strength="moderate", confidence=0.5, observations=["GROUP BY usage"]),
        ]
    )
    claimed = [ClaimedSkill(skill="Python", level="advanced"), ClaimedSkill(skill="SQL", level="advanced")]

    with (
        patch("app.services.github_analyzer.GithubClient", new=_fake_client_factory()),
        patch("app.services.github_analyzer.call_structured", new=AsyncMock(return_value=ai_output)),
    ):
        languages, skills, claims_vs_evidence, used_fallback = asyncio.run(
            analyze_repository("https://github.com/example/repo", claimed, ["Python", "SQL"])
        )

    assert used_fallback is False
    # Languages come from the GitHub API's own byte stats, not from Claude.
    assert languages[0].language == "Python"
    assert languages[0].confidence == 0.9
    assert {s.skill for s in skills} == {"Python", "SQL"}

    by_skill = {c.skill: c for c in claims_vs_evidence}
    assert by_skill["Python"].assessment == "Strong evidence supports this claim"
    assert by_skill["SQL"].assessment == "Partially supported — verify via a practical challenge"


def test_analyze_repository_falls_back_to_fixture_when_claude_unavailable():
    claimed = [ClaimedSkill(skill="Python", level="advanced")]

    with (
        patch("app.services.github_analyzer.GithubClient", new=_fake_client_factory()),
        patch(
            "app.services.github_analyzer.call_structured",
            new=AsyncMock(side_effect=AIServiceUnavailable("no key configured")),
        ),
    ):
        languages, skills, claims_vs_evidence, used_fallback = asyncio.run(
            analyze_repository("https://github.com/example/repo", claimed, ["Python"])
        )

    assert used_fallback is True
    assert languages  # still computed from the (fake) GitHub API response, not fallback
    assert any(s.skill == "Python" for s in skills)  # from the fixture


def test_analyze_repository_claim_with_no_repository_evidence():
    ai_output = GithubAnalysisAIOutput(
        skills=[SkillEvidenceItem(skill="Python", evidence_strength="none", confidence=0.0, observations=[])]
    )
    claimed = [ClaimedSkill(skill="Python", level="beginner")]

    with (
        patch("app.services.github_analyzer.GithubClient", new=_fake_client_factory()),
        patch("app.services.github_analyzer.call_structured", new=AsyncMock(return_value=ai_output)),
    ):
        _, _, claims_vs_evidence, _ = asyncio.run(
            analyze_repository("https://github.com/example/repo", claimed, [])
        )

    assert claims_vs_evidence[0].assessment == "Claim not yet supported by repository evidence"


def test_analyze_repository_propagates_access_errors_without_fabricating_evidence():
    with patch(
        "app.services.github_analyzer.GithubClient",
        new=_fake_client_factory(fail_with=GithubAccessError("repo not found")),
    ):
        with pytest.raises(GithubAccessError):
            asyncio.run(analyze_repository("https://github.com/example/repo", [], []))
