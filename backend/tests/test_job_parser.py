"""Per BLUEPRINT.md Section U: AI service tests mock the Claude client and
assert Pydantic validation / downstream parsing — they never assess actual
Claude output quality (that's eyeballed during integration)."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.ai.claude_client import AIServiceUnavailable
from app.schemas.job import JobRequiredSkill, ParsedJob
from app.services.job_parser import parse_job

SAMPLE_JDS = {
    "data_analyst": (
        "We are hiring a Data Analyst. Must have strong SQL and Python skills, "
        "familiarity with statistics, and experience building dashboards in "
        "Power BI. Strong problem solving skills required. 2+ years of "
        "experience preferred.",
        ParsedJob(
            title="Data Analyst",
            required_skills=[
                JobRequiredSkill(skill="SQL", importance="high"),
                JobRequiredSkill(skill="Python", importance="high"),
                JobRequiredSkill(skill="Statistics", importance="medium"),
                JobRequiredSkill(skill="Power BI", importance="medium"),
                JobRequiredSkill(skill="Problem Solving", importance="high"),
            ],
            soft_skills=[],
            tools=["Power BI"],
            experience_years=2,
        ),
    ),
    "backend_engineer": (
        "Backend Engineer needed. Required: Python, PostgreSQL, Docker. Nice "
        "to have: Kubernetes experience. Must communicate clearly with "
        "cross-functional teams. 5 years experience required.",
        ParsedJob(
            title="Backend Engineer",
            required_skills=[
                JobRequiredSkill(skill="Python", importance="high"),
                JobRequiredSkill(skill="SQL", importance="high"),
                JobRequiredSkill(skill="Docker", importance="high"),
                JobRequiredSkill(skill="Kubernetes", importance="low", required=False),
            ],
            soft_skills=["Communication"],
            tools=["PostgreSQL", "Docker"],
            experience_years=5,
        ),
    ),
}


@pytest.mark.parametrize("raw_description,expected", SAMPLE_JDS.values(), ids=SAMPLE_JDS.keys())
def test_parse_job_returns_claude_structured_output(raw_description, expected):
    with patch("app.services.job_parser.call_structured", new=AsyncMock(return_value=expected)):
        job, used_fallback = asyncio.run(parse_job(raw_description))

    assert used_fallback is False
    assert job == expected


def test_parse_job_falls_back_to_fixture_when_claude_unavailable():
    with patch(
        "app.services.job_parser.call_structured",
        new=AsyncMock(side_effect=AIServiceUnavailable("no API key configured")),
    ):
        job, used_fallback = asyncio.run(parse_job("any description"))

    assert used_fallback is True
    assert job.title == "Data Analyst"
    assert any(skill.skill == "SQL" for skill in job.required_skills)
