"""Router-level test with no mocking — relies on this environment having no
ANTHROPIC_API_KEY, exercising the real fixture-fallback path end-to-end
through the actual HTTP contract."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_mutate_challenge_end_to_end_with_no_api_key_configured():
    previous_challenge = {
        "id": str(uuid4()),
        "job_id": str(uuid4()),
        "parent_challenge_id": None,
        "title": "Investigate the Revenue Discrepancy",
        "role": "Junior Data Analyst",
        "scenario": "Revenue looks inflated.",
        "instructions": "...",
        "required_skills": ["SQL", "Statistics"],
        "difficulty": 1,
        "dataset": {"tables": []},
        "expected_output": "...",
        "evaluation_criteria": {
            "correctness": 0.3, "technical_logic": 0.25, "reasoning": 0.2,
            "edge_cases": 0.15, "efficiency": 0.1,
        },
        "mutation_reason": None,
    }
    previous_evaluation = {
        "submission_id": str(uuid4()),
        "evaluation_id": str(uuid4()),
        "rubric_scores": {"correctness": 70, "technical_logic": 70, "reasoning": 70, "edge_cases": 55, "efficiency": 70},
        "overall_score": 61.0,
        "strengths": ["Correct JOIN"],
        "weaknesses": ["Did not address statistical significance"],
        "evidence": [],
        "skill_gaps": [{"skill": "Statistics", "missing_concepts": ["Hypothesis testing"]}],
        "sql_execution_result": None,
        "demo_fallback": False,
    }

    request_body = {
        "user_id": str(uuid4()),
        "job_id": str(uuid4()),
        "job_title": "Data Analyst",
        "required_skills": ["SQL", "Python", "Statistics"],
        "previous_attempt": {"challenge": previous_challenge, "evaluation": previous_evaluation},
    }

    response = client.post("/challenges/mutate", json=request_body)

    assert response.status_code == 200
    body = response.json()
    assert body["demo_fallback"] is True
    assert body["challenge"]["parent_challenge_id"] == previous_challenge["id"]
    assert body["challenge"]["mutation_reason"]
    # 61.0 is not < 60, so difficulty stays at 1 — backend arithmetic, not fixture content.
    assert body["challenge"]["difficulty"] == 1
    assert body["challenge"]["evaluation_criteria"] == previous_challenge["evaluation_criteria"]
