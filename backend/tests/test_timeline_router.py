"""Router-level test proving /timeline/compute is actually wired into
main.py and its request/response schemas round-trip over real HTTP —
complements the pure-function coverage in test_timeline_engine.py."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_compute_timeline_endpoint_returns_no_skills_with_no_history():
    response = client.post(
        "/timeline/compute", json={"user_id": str(uuid4()), "submission_history": []}
    )

    assert response.status_code == 200
    assert response.json()["skills"] == []


def test_compute_timeline_endpoint_builds_a_history_from_a_real_submission_payload():
    challenge = {
        "id": str(uuid4()), "job_id": str(uuid4()), "parent_challenge_id": None,
        "title": "Investigate the Revenue Discrepancy", "role": "Junior Data Analyst",
        "scenario": "...", "instructions": "...", "required_skills": ["SQL"], "difficulty": 1,
        "dataset": {"tables": []}, "expected_output": "...",
        "evaluation_criteria": {
            "correctness": 0.3, "technical_logic": 0.25, "reasoning": 0.2,
            "edge_cases": 0.15, "efficiency": 0.1,
        },
        "mutation_reason": None,
    }
    evaluation = {
        "submission_id": str(uuid4()), "evaluation_id": str(uuid4()),
        "rubric_scores": {"correctness": 80, "technical_logic": 80, "reasoning": 80, "edge_cases": 80, "efficiency": 80},
        "overall_score": 80.0, "strengths": [], "weaknesses": [], "evidence": [], "skill_gaps": [],
        "sql_execution_result": None, "demo_fallback": False,
    }

    response = client.post(
        "/timeline/compute",
        json={
            "user_id": str(uuid4()),
            "submission_history": [{"challenge": challenge, "evaluation": evaluation}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["skills"]) == 1
    assert body["skills"][0]["skill"] == "SQL"
    assert body["skills"][0]["entries"][0]["score"] == 80.0
    assert body["skills"][0]["entries"][0]["challenge_title"] == "Investigate the Revenue Discrepancy"
