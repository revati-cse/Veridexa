from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import Importance


class JobRequiredSkill(BaseModel):
    skill: str
    importance: Importance
    required: bool = True


class JobParseRequest(BaseModel):
    raw_description: str = Field(min_length=20, max_length=8000)


class ParsedJob(BaseModel):
    """Structured output of job_parser.py — validated against Claude's JSON response."""

    title: str
    required_skills: list[JobRequiredSkill]
    soft_skills: list[str] = []
    tools: list[str] = []
    experience_years: int | None = None


class JobParseResponse(BaseModel):
    job_id: UUID
    job: ParsedJob
    demo_fallback: bool = False
