"""Router-level test with no mocking at all — relies on this environment
having no ANTHROPIC_API_KEY configured, so it exercises the real fixture-
fallback path end-to-end through the actual HTTP contract, including a real
sql_runner execution. Complements the mocked unit tests in
test_evaluation_engine.py, which cover the Claude-success path."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_submit_solution_end_to_end_with_no_api_key_configured():
    challenge = {
        "id": str(uuid4()),
        "job_id": str(uuid4()),
        "parent_challenge_id": None,
        "title": "Investigate the Revenue Discrepancy",
        "role": "Junior Data Analyst",
        "scenario": "Revenue looks inflated.",
        "instructions": "Write a query that computes revenue per customer.",
        "required_skills": ["SQL"],
        "difficulty": 1,
        "dataset": {
            "tables": [
                {"name": "customers", "columns": ["id", "name"], "rows": [[1, "Alice"], [2, "Bob"]]},
                {"name": "orders", "columns": ["id", "customer_id", "amount"], "rows": [[1, 1, 100], [2, 2, 50]]},
            ]
        },
        "expected_output": "Revenue per customer.",
        "evaluation_criteria": {
            "correctness": 0.3, "technical_logic": 0.25, "reasoning": 0.2,
            "edge_cases": 0.15, "efficiency": 0.1,
        },
        "mutation_reason": None,
    }
    request_body = {
        "challenge": challenge,
        "user_id": str(uuid4()),
        "code": "SELECT c.name, o.amount FROM customers c JOIN orders o ON o.customer_id = c.id",
        "explanation": "I joined customers to orders.",
    }

    response = client.post("/submissions", json=request_body)

    assert response.status_code == 200
    body = response.json()
    assert body["demo_fallback"] is True
    assert body["sql_execution_result"]["success"] is True
    assert body["sql_execution_result"]["row_count"] == 2
    assert 0 <= body["overall_score"] <= 100
    assert set(body["rubric_scores"].keys()) == {
        "correctness", "technical_logic", "reasoning", "edge_cases", "efficiency",
    }
