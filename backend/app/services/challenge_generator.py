"""challenge_generator service — BLUEPRINT.md Feature 3.

Pure function: job title + target skills + difficulty in, a full Challenge
out. Only the scenario/instructions/dataset come from Claude
(ChallengeAIOutput) — difficulty and evaluation_criteria are backend-
assigned, matching the same "never let the LLM own the arithmetic/rubric"
principle used for readiness scoring.
"""

import json
import logging
from pathlib import Path
from uuid import UUID, uuid4

from app.ai.claude_client import AIServiceUnavailable, call_structured
from app.ai.prompts.challenge_generation_prompt import SYSTEM_PROMPT, build_user_prompt
from app.schemas.challenge import Challenge, ChallengeAIOutput
from app.schemas.common import Difficulty
from app.schemas.evaluation import DEFAULT_RUBRIC_WEIGHTS

logger = logging.getLogger(__name__)

_FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "demo_challenge.json"


def _load_fixture() -> ChallengeAIOutput:
    data = json.loads(_FIXTURE_PATH.read_text())
    return ChallengeAIOutput.model_validate(data)


async def generate_challenge(
    job_id: UUID,
    job_title: str,
    required_skills: list[str],
    difficulty: Difficulty,
) -> tuple[Challenge, bool]:
    """Returns (challenge, used_fallback)."""
    try:
        ai_output = await call_structured(
            system=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(job_title, required_skills, difficulty),
            response_model=ChallengeAIOutput,
        )
        used_fallback = False
    except AIServiceUnavailable as exc:
        logger.warning("challenge_generator falling back to fixture: %s", exc)
        ai_output = _load_fixture()
        used_fallback = True

    challenge = Challenge(
        id=uuid4(),
        job_id=job_id,
        parent_challenge_id=None,
        title=ai_output.title,
        role=ai_output.role,
        scenario=ai_output.scenario,
        instructions=ai_output.instructions,
        required_skills=ai_output.required_skills,
        difficulty=difficulty,
        dataset=ai_output.dataset.model_dump(),
        expected_output=ai_output.expected_output,
        evaluation_criteria=DEFAULT_RUBRIC_WEIGHTS,
        mutation_reason=None,
    )
    return challenge, used_fallback
