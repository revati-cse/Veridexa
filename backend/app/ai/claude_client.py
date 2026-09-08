"""Single Claude API call site, per BLUEPRINT.md Section H.

Every AI service goes through `call_structured()` instead of calling the
Anthropic SDK directly, so the retry/fallback policy lives in one place.
Uses `client.messages.parse(..., output_format=<PydanticModel>)` (Structured
Outputs) rather than prompt-only JSON coaxing + manual json.loads — the API
itself constrains the response to the given schema, so `response.parsed_output`
is already a validated instance of the model.
"""

import logging
from typing import TypeVar

import anthropic
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-5"
DEFAULT_MAX_TOKENS = 4096
MAX_ATTEMPTS = 2

TResponse = TypeVar("TResponse", bound=BaseModel)


class AIServiceUnavailable(Exception):
    """Raised when Claude did not produce a valid structured response after
    retries (or no API key is configured). Callers catch this and fall back
    to a fixture per BLUEPRINT.md Section W — it must never surface as a
    raw 500 to the frontend."""


async def call_structured(
    *,
    system: str,
    user_prompt: str,
    response_model: type[TResponse],
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> TResponse:
    """Calls Claude once, retrying up to MAX_ATTEMPTS total on a retryable
    failure (429/5xx/connection/validation), then raises AIServiceUnavailable.

    Network-level retries (connection errors, 429, 5xx) are also covered by
    the SDK's own default `max_retries=2` — the loop here exists for the
    cases that aren't: a bad/missing structured response, or exhausting the
    SDK's retries entirely.
    """
    if not settings.anthropic_api_key:
        raise AIServiceUnavailable("ANTHROPIC_API_KEY is not configured.")

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    messages = [{"role": "user", "content": user_prompt}]

    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = await client.messages.parse(
                model=MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
                output_format=response_model,
            )
            return response.parsed_output
        except anthropic.APIStatusError as exc:
            last_error = exc
            if exc.status_code != 429 and exc.status_code < 500:
                # Non-retryable: bad request, auth failure, etc.
                break
            logger.warning("Claude call attempt %s/%s failed (status=%s)", attempt, MAX_ATTEMPTS, exc.status_code)
        except Exception as exc:  # noqa: BLE001 - covers connection errors and response validation failures
            last_error = exc
            logger.warning("Claude call attempt %s/%s failed: %s", attempt, MAX_ATTEMPTS, exc)

    raise AIServiceUnavailable(
        f"Claude did not return a valid {response_model.__name__} after {MAX_ATTEMPTS} attempt(s): {last_error}"
    ) from last_error
