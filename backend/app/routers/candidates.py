from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas import ClaimsRequest

router = APIRouter(prefix="/candidates", tags=["candidates"])


class ClaimsSavedResponse(BaseModel):
    """Lightweight ack — not part of the frozen cross-language contract in
    lib/types.ts since it carries no data the UI needs back beyond a count."""

    status: str = "ok"
    claims_saved: int


@router.post("/claims", response_model=ClaimsSavedResponse)
async def save_claims(request: ClaimsRequest) -> ClaimsSavedResponse:
    """STUB: acknowledges receipt only. Real implementation (Phase 6) persists
    each ClaimedSkill against the normalized skill_id in `skills`."""
    return ClaimsSavedResponse(claims_saved=len(request.claims))
