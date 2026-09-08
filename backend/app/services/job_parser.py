"""job_parser service — BLUEPRINT.md Feature 1.

Pure function: raw JD text in, ParsedJob out (plus whether a fallback was
used). No FastAPI objects and no DB access here — the router is responsible
for persistence and for generating job_id.
"""

import json
import logging
from pathlib import Path

from app.ai.claude_client import AIServiceUnavailable, call_structured
from app.ai.prompts.job_parser_prompt import SYSTEM_PROMPT, build_user_prompt
from app.schemas.job import ParsedJob

logger = logging.getLogger(__name__)

_FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "demo_job.json"


def _load_fixture() -> ParsedJob:
    data = json.loads(_FIXTURE_PATH.read_text())
    return ParsedJob.model_validate(data)


async def parse_job(raw_description: str) -> tuple[ParsedJob, bool]:
    """Returns (parsed_job, used_fallback)."""
    try:
        job = await call_structured(
            system=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(raw_description),
            response_model=ParsedJob,
        )
        return job, False
    except AIServiceUnavailable as exc:
        logger.warning("job_parser falling back to fixture: %s", exc)
        return _load_fixture(), True
