from fastapi import APIRouter
from pydantic import BaseModel

from app.db import safe_write
from app.db.claims import save_claims as save_claims_to_db
from app.schemas import ClaimsRequest

router = APIRouter(prefix="/candidates", tags=["candidates"])


class ClaimsSavedResponse(BaseModel):
    """Lightweight ack — not part of the frozen cross-language contract in
    lib/types.ts since it carries no data the UI needs back beyond a count."""

    status: str = "ok"
    claims_saved: int


@router.post("/claims", response_model=ClaimsSavedResponse)
async def save_claims(request: ClaimsRequest) -> ClaimsSavedResponse:
    """Best-effort persistence, same as every other db/*.py write in this
    API — the frontend's session store (not this table) stays the primary
    read path for the candidate's own flow; persisted claims exist so the
    recruiter dashboard's claim-alignment bonus has something real to read
    per candidate instead of always passing claims=[]."""
    await safe_write(save_claims_to_db(request.user_id, request.claims))
    return ClaimsSavedResponse(claims_saved=len(request.claims))
