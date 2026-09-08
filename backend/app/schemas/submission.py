from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.challenge import Challenge


class SubmissionCreate(BaseModel):
    # No DB persistence yet, so there's no way to look a challenge up by id —
    # the frontend already holds the full Challenge in its session store
    # (it just received it from /challenges/generate or /challenges/mutate),
    # so it's passed through directly. challenge.id is the challenge_id.
    challenge: Challenge
    user_id: UUID
    code: str = Field(default="", max_length=10000)
    explanation: str = Field(default="", max_length=4000)
