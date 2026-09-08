#!/usr/bin/env python3
"""End-to-end smoke test against a *running* backend (BLUEPRINT.md Section U
/ checklist item 29) — not a unit test, not TestClient. Run this before every
milestone commit and definitely before the final demo freeze:

    uvicorn app.main:app &            # from backend/, in one terminal
    python scripts/smoke_test.py      # from backend/, in another

Runs the exact BLUEPRINT.md Section W demo path (Data Analyst JD -> challenge
-> submit -> evaluate -> readiness -> gap -> mutate -> resubmit -> improved
readiness) over real HTTP against whatever ANTHROPIC_API_KEY/DATABASE_URL
config the running server has — live Claude if configured, the fixture
fallback otherwise (demo_fallback: true on the response either way tells you
which). Exits non-zero with a clear message on the first failed step.
"""

import os
import sys
from uuid import uuid4

import httpx

BASE_URL = os.environ.get("SMOKE_TEST_BASE_URL", "http://localhost:8000")

DEMO_JD = (
    "We are hiring a Data Analyst to join our growing analytics team. "
    "The ideal candidate has strong SQL and Python skills, is comfortable "
    "with statistics (hypothesis testing, significance), and can build "
    "dashboards in Power BI. Strong problem-solving skills required. "
    "2+ years of experience preferred."
)

CLAIMED_SKILLS = [
    {"skill": "SQL", "level": "intermediate"},
    {"skill": "Python", "level": "advanced"},
    {"skill": "Statistics", "level": "beginner"},
    {"skill": "Power BI", "level": "intermediate"},
    {"skill": "Problem Solving", "level": "advanced"},
]

DEMO_REPO_URL = "https://github.com/octocat/Hello-World"

# Deliberately naive — matches demo_evaluation.json's fixture narrative
# ("didn't dedupe the repeated order, didn't handle the null customer_id")
# so the fallback path and a good-faith live-Claude score tell the same story.
FIRST_SUBMISSION_SQL = (
    "SELECT c.name, SUM(o.amount) AS revenue FROM customers c "
    "JOIN orders o ON o.customer_id = c.id GROUP BY c.name"
)
FIRST_SUBMISSION_EXPLANATION = (
    "I joined customers to orders and summed the amount per customer to get "
    "each customer's total revenue."
)

SECOND_SUBMISSION_SQL = (
    "SELECT month, AVG(amount) AS avg_amount, COUNT(*) AS n "
    "FROM monthly_orders GROUP BY month"
)
SECOND_SUBMISSION_EXPLANATION = (
    "I compared the average order amount and sample size for each month to "
    "reason about whether the increase is larger than normal month-to-month "
    "variation, rather than assuming any increase is meaningful."
)


def step(label: str):
    print(f"\n=== {label} ===")


def fail(label: str, detail: str) -> None:
    print(f"\nFAILED at: {label}\n{detail}")
    sys.exit(1)


def main() -> None:
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)
    user_id = str(uuid4())

    step("Health check")
    resp = client.get("/health")
    if resp.status_code != 200:
        fail("health check", f"{resp.status_code}: {resp.text}")
    print(f"backend is up at {BASE_URL}")

    step("POST /jobs/parse")
    resp = client.post("/jobs/parse", json={"raw_description": DEMO_JD})
    if resp.status_code != 200:
        fail("jobs/parse", f"{resp.status_code}: {resp.text}")
    job_body = resp.json()
    job_id = job_body["job_id"]
    job = job_body["job"]
    required_skills = job["required_skills"]
    print(f"job_id={job_id} title={job['title']!r} demo_fallback={job_body['demo_fallback']}")
    print("required skills:", [s["skill"] for s in required_skills])

    step("POST /github/analyze (best-effort)")
    github_evidence = None
    resp = client.post(
        "/github/analyze",
        json={
            "user_id": user_id,
            "repository_url": DEMO_REPO_URL,
            "claimed_skills": CLAIMED_SKILLS,
            "required_skills": [s["skill"] for s in required_skills],
        },
    )
    if resp.status_code == 200:
        github_evidence = resp.json()
        print(f"repository_id={github_evidence['repository_id']} demo_fallback={github_evidence['demo_fallback']}")
    else:
        # Matches BLUEPRINT.md Section V: a repo we can't reach is a real
        # error, and the candidate continues without GitHub evidence.
        print(f"github/analyze unavailable ({resp.status_code}) — continuing without GitHub evidence, as designed")

    step("POST /challenges/generate")
    resp = client.post(
        "/challenges/generate",
        json={
            "job_id": job_id,
            "job_title": job["title"],
            "user_id": user_id,
            "required_skills": [s["skill"] for s in required_skills],
            "difficulty": 1,
        },
    )
    if resp.status_code != 200:
        fail("challenges/generate", f"{resp.status_code}: {resp.text}")
    challenge_body = resp.json()
    challenge = challenge_body["challenge"]
    print(f"challenge_id={challenge['id']} title={challenge['title']!r} demo_fallback={challenge_body['demo_fallback']}")

    step("POST /submissions (first attempt)")
    resp = client.post(
        "/submissions",
        json={
            "challenge": challenge,
            "user_id": user_id,
            "code": FIRST_SUBMISSION_SQL,
            "explanation": FIRST_SUBMISSION_EXPLANATION,
        },
    )
    if resp.status_code != 200:
        fail("submissions (first)", f"{resp.status_code}: {resp.text}")
    first_evaluation = resp.json()
    print(f"overall_score={first_evaluation['overall_score']} demo_fallback={first_evaluation['demo_fallback']}")
    print(f"sql executed: success={first_evaluation['sql_execution_result']['success']}")

    step("POST /readiness/compute (before mutation)")
    readiness_request_before = {
        "user_id": user_id,
        "job_id": job_id,
        "job_title": job["title"],
        "required_skills": required_skills,
        "claims": CLAIMED_SKILLS,
        "github_evidence": github_evidence,
        "submission_history": [{"challenge": challenge, "evaluation": first_evaluation}],
    }
    resp = client.post("/readiness/compute", json=readiness_request_before)
    if resp.status_code != 200:
        fail("readiness/compute (before)", f"{resp.status_code}: {resp.text}")
    readiness_before = resp.json()
    print(f"readiness_score (before) = {readiness_before['readiness_score']}")
    for row in readiness_before["skill_breakdown"]:
        print(f"  {row['skill']:<16} {row['score']:>6.1f}")
    print("skill_gaps:", [g["skill"] for g in readiness_before["skill_gaps"]])

    step("POST /challenges/mutate")
    resp = client.post(
        "/challenges/mutate",
        json={
            "user_id": user_id,
            "job_id": job_id,
            "job_title": job["title"],
            "required_skills": [s["skill"] for s in required_skills],
            "previous_attempt": {"challenge": challenge, "evaluation": first_evaluation},
        },
    )
    if resp.status_code != 200:
        fail("challenges/mutate", f"{resp.status_code}: {resp.text}")
    mutated_body = resp.json()
    mutated_challenge = mutated_body["challenge"]
    print(f"mutated challenge_id={mutated_challenge['id']} title={mutated_challenge['title']!r}")
    print(f"mutation_reason: {mutated_challenge['mutation_reason']}")
    if mutated_challenge["parent_challenge_id"] != challenge["id"]:
        fail("challenges/mutate", "parent_challenge_id does not point back to the original challenge")

    step("POST /submissions (resubmission against the mutated challenge)")
    resp = client.post(
        "/submissions",
        json={
            "challenge": mutated_challenge,
            "user_id": user_id,
            "code": SECOND_SUBMISSION_SQL,
            "explanation": SECOND_SUBMISSION_EXPLANATION,
        },
    )
    if resp.status_code != 200:
        fail("submissions (second)", f"{resp.status_code}: {resp.text}")
    second_evaluation = resp.json()
    print(f"overall_score={second_evaluation['overall_score']} demo_fallback={second_evaluation['demo_fallback']}")

    step("POST /readiness/compute (after mutation)")
    readiness_request_after = {
        **readiness_request_before,
        "submission_history": [
            {"challenge": challenge, "evaluation": first_evaluation},
            {"challenge": mutated_challenge, "evaluation": second_evaluation},
        ],
    }
    resp = client.post("/readiness/compute", json=readiness_request_after)
    if resp.status_code != 200:
        fail("readiness/compute (after)", f"{resp.status_code}: {resp.text}")
    readiness_after = resp.json()
    print(f"readiness_score (after) = {readiness_after['readiness_score']}")
    for row in readiness_after["skill_breakdown"]:
        print(f"  {row['skill']:<16} {row['score']:>6.1f}")
    print("skill_gaps:", [g["skill"] for g in readiness_after["skill_gaps"]])

    step("GET /challenges/{id}/history")
    resp = client.get(f"/challenges/{mutated_challenge['id']}/history")
    if resp.status_code != 200:
        fail("challenges/history", f"{resp.status_code}: {resp.text}")
    chain = resp.json()["chain"]
    if chain:
        print(f"history chain: {[c['id'] for c in chain]} (DATABASE_URL is configured)")
    else:
        print("history chain empty (DATABASE_URL not configured on this server — expected, not a failure)")

    step("Summary")
    print(f"readiness: {readiness_before['readiness_score']} -> {readiness_after['readiness_score']}")
    if readiness_after["readiness_score"] <= readiness_before["readiness_score"]:
        fail(
            "summary",
            "readiness did not improve after mutation+resubmission — "
            f"before={readiness_before['readiness_score']} after={readiness_after['readiness_score']}",
        )

    print("\nSMOKE TEST PASSED — full demo loop works end-to-end.")


if __name__ == "__main__":
    main()
