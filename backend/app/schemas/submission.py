from uuid import UUID

from pydantic import BaseModel, Field


class SubmissionCreate(BaseModel):
    challenge_id: UUID
    user_id: UUID
    code: str = Field(default="", max_length=10000)
    explanation: str = Field(default="", max_length=4000)
