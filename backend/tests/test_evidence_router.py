from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_VALID_REQUEST = {
    "user_id": "11111111-1111-1111-1111-111111111111",
    "description": "Built a sales dashboard in Power BI and cleaned the source data with a Python script.",
    "claimed_skills": [{"skill": "Python", "level": "intermediate"}],
    "required_skills": ["Python", "Power BI"],
}


def test_analyze_description_returns_200_with_expected_shape():
    from app.schemas.github import ClaimVsEvidenceItem, SkillEvidenceItem

    fake_result = (
        [SkillEvidenceItem(skill="Python", evidence_strength="moderate", confidence=0.5, observations=["x"])],
        [ClaimVsEvidenceItem(skill="Python", claim="intermediate", repository_evidence="moderate", assessment="x")],
        False,
    )
    with patch("app.routers.evidence.analyze_description", new=AsyncMock(return_value=fake_result)):
        response = client.post("/evidence/analyze-description", json=_VALID_REQUEST)

    assert response.status_code == 200
    body = response.json()
    assert body["demo_fallback"] is False
    assert body["skills"][0]["skill"] == "Python"
    assert "source_id" in body


def test_description_shorter_than_minimum_length_is_rejected():
    bad_request = {**_VALID_REQUEST, "description": "too short"}
    response = client.post("/evidence/analyze-description", json=bad_request)

    assert response.status_code == 422
