"""challenge_mutation_engine service — BLUEPRINT.md Feature 8 / Section P.

THE core product differentiator: unlike a plain difficulty slider, the next
challenge is written to specifically probe what the candidate got wrong on
the previous attempt. Difficulty stepping (adapt_difficulty) is a separate,
much simpler concern (Section 3) from the mutation *content* itself
(Section 8) — conflating them would bury the actual innovation inside a
score threshold.

Per Section P's own pseudocode, the mutation target is the previous
evaluation's own skill_gaps[0] — reused directly, never re-derived with a
fresh Claude call. This is deliberately narrower than skill_gap_engine's
aggregate, cross-history ranking (used by the readiness dashboard): a
mutation reacts to the ONE attempt that just happened.
"""

import json
import logging
from pathlib import Path
from uuid import UUID, uuid4

from app.ai.claude_client import AIServiceUnavailable, call_structured
from app.ai.prompts.mutation_prompt import SYSTEM_PROMPT, build_user_prompt
from app.schemas.challenge import Challenge, MutatedChallengeAIOutput
from app.schemas.common import Difficulty
from app.schemas.evaluation import DEFAULT_RUBRIC_WEIGHTS, SubmissionRecord

logger = logging.getLogger(__name__)

_FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "demo_mutation.json"

MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 3
HIGH_SCORE_THRESHOLD = 85.0
LOW_SCORE_THRESHOLD = 60.0


def adapt_difficulty(score: float, current: Difficulty) -> Difficulty:
    """Section 3's basic difficulty step. score >= 85 -> harder, score < 60
    -> easier, otherwise unchanged. Independent of what the mutation
    actually targets content-wise."""
    if score >= HIGH_SCORE_THRESHOLD:
        return min(current + 1, MAX_DIFFICULTY)
    if score < LOW_SCORE_THRESHOLD:
        return max(current - 1, MIN_DIFFICULTY)
    return current


def _load_fixture() -> MutatedChallengeAIOutput:
    data = json.loads(_FIXTURE_PATH.read_text())
    return MutatedChallengeAIOutput.model_validate(data)


async def mutate_challenge(
    job_id: UUID,
    job_title: str,
    required_skills: list[str],
    previous_attempt: SubmissionRecord,
) -> tuple[Challenge, bool]:
    """Returns (challenge, used_fallback)."""
    previous_challenge = previous_attempt.challenge
    evaluation = previous_attempt.evaluation
    next_difficulty = adapt_difficulty(evaluation.overall_score, previous_challenge.difficulty)
    target_gap = evaluation.skill_gaps[0] if evaluation.skill_gaps else None

    try:
        ai_output = await call_structured(
            system=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(
                previous_scenario=previous_challenge.scenario,
                previous_required_skills=previous_challenge.required_skills,
                weaknesses=evaluation.weaknesses,
                target_skill=target_gap.skill if target_gap else None,
                missing_concepts=target_gap.missing_concepts if target_gap else [],
                job_title=job_title,
                required_skills=required_skills,
                difficulty=next_difficulty,
            ),
            response_model=MutatedChallengeAIOutput,
        )
        used_fallback = False
    except AIServiceUnavailable as exc:
        logger.warning("challenge_mutation_engine falling back to fixture: %s", exc)
        ai_output = _load_fixture()
        used_fallback = True

    challenge = Challenge(
        id=uuid4(),
        job_id=job_id,
        parent_challenge_id=previous_challenge.id,
        title=ai_output.title,
        role=ai_output.role,
        scenario=ai_output.scenario,
        instructions=ai_output.instructions,
        required_skills=ai_output.required_skills,
        difficulty=next_difficulty,
        dataset=ai_output.dataset.model_dump(),
        expected_output=ai_output.expected_output,
        evaluation_criteria=DEFAULT_RUBRIC_WEIGHTS,
        mutation_reason=ai_output.mutation_reason,
    )
    return challenge, used_fallback
