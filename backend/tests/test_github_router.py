from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.github.client import GithubAccessError
from app.main import app

client = TestClient(app)

_VALID_REQUEST = {
    "user_id": "11111111-1111-1111-1111-111111111111",
    "repository_url": "https://github.com/example/repo",
    "claimed_skills": [{"skill": "Python", "level": "advanced"}],
    "required_skills": ["Python"],
}


def test_inaccessible_repository_returns_422_not_fabricated_evidence():
    with patch(
        "app.routers.github.analyze_repository",
        new=AsyncMock(side_effect=GithubAccessError("Repository example/repo was not found (or is private).")),
    ):
        response = client.post("/github/analyze", json=_VALID_REQUEST)

    assert response.status_code == 422
    assert "not found" in response.json()["detail"].lower()


def test_successful_analysis_returns_200_with_expected_shape():
    from app.schemas.github import ClaimVsEvidenceItem, LanguageDetected, SkillEvidenceItem

    fake_result = (
        [LanguageDetected(language="Python", confidence=0.9)],
        [SkillEvidenceItem(skill="Python", evidence_strength="strong", confidence=0.9, observations=["x"])],
        [ClaimVsEvidenceItem(skill="Python", claim="advanced", repository_evidence="strong", assessment="Strong evidence supports this claim")],
        False,
    )
    with patch("app.routers.github.analyze_repository", new=AsyncMock(return_value=fake_result)):
        response = client.post("/github/analyze", json=_VALID_REQUEST)

    assert response.status_code == 200
    body = response.json()
    assert body["repository"] == _VALID_REQUEST["repository_url"]
    assert body["demo_fallback"] is False
    assert body["skills"][0]["skill"] == "Python"


def test_invalid_repository_url_is_rejected_before_reaching_the_service():
    bad_request = {**_VALID_REQUEST, "repository_url": "not-a-url"}
    response = client.post("/github/analyze", json=bad_request)

    assert response.status_code == 422
