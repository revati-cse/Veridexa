"""Router-level test proving /freshness/compute is actually wired into
main.py and its request/response schemas round-trip over real HTTP —
complements the pure-function coverage in test_freshness_engine.py."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_compute_freshness_endpoint_returns_not_assessed_with_no_evidence():
    request_body = {
        "user_id": str(uuid4()),
        "required_skills": [{"skill": "SQL", "importance": "high", "required": True}],
        "github_evidence": None,
        "submission_history": [],
    }

    response = client.post("/freshness/compute", json=request_body)

    assert response.status_code == 200
    body = response.json()
    assert len(body["skills"]) == 1
    assert body["skills"][0]["skill"] == "SQL"
    assert body["skills"][0]["freshness"] == "not_assessed"
    assert body["skills"][0]["last_evidence_at"] is None
