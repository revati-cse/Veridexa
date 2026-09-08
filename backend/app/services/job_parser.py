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
from app.services.skill_engine import normalize_required_skills

logger = logging.getLogger(__name__)

_FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "demo_job.json"


def _load_fixture() -> ParsedJob:
    data = json.loads(_FIXTURE_PATH.read_text())
    return ParsedJob.model_validate(data)


async def parse_job(raw_description: str) -> tuple[ParsedJob, bool]:
    """Returns (parsed_job, used_fallback). required_skills is normalized and
    de-duplicated against the skill taxonomy (skill_engine.py) before being
    returned — Claude is asked for commonly-known names, but this is the
    deterministic backend safety net, not a formatting nicety: without it,
    "MySQL" and "PostgreSQL" in the same JD would show up as two separate
    skill rows instead of merging into one "SQL" requirement."""
    try:
        job = await call_structured(
            system=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(raw_description),
            response_model=ParsedJob,
        )
        used_fallback = False
    except AIServiceUnavailable as exc:
        logger.warning("job_parser falling back to fixture: %s", exc)
        job = _load_fixture()
        used_fallback = True

    job = job.model_copy(update={"required_skills": normalize_required_skills(job.required_skills)})
    return job, used_fallback
