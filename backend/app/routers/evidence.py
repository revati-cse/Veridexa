from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter

from app.schemas import EvidenceItem, EvidenceListResponse, SkillEvidenceGroup

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("/{user_id}", response_model=EvidenceListResponse)
async def get_evidence(user_id: UUID) -> EvidenceListResponse:
    """STUB: real implementation (Phase 9) queries the `evidence` table,
    grouped by skill_id. Every confidence % on the dashboard must trace back
    to a non-empty list here — never render a % with nothing backing it."""
    now = datetime.now(timezone.utc)
    return EvidenceListResponse(
        user_id=user_id,
        skills=[
            SkillEvidenceGroup(
                skill="SQL",
                evidence=[
                    EvidenceItem(
                        id=uuid4(), skill="SQL", source_type="challenge",
                        source_reference=None,
                        observation="Correct JOIN and GROUP BY usage in the revenue discrepancy challenge",
                        confidence=0.85, created_at=now,
                    ),
                    EvidenceItem(
                        id=uuid4(), skill="SQL", source_type="github",
                        source_reference="https://github.com/example/example-repo",
                        observation="JOIN and GROUP BY patterns found in repository SQL files",
                        confidence=0.6, created_at=now,
                    ),
                ],
            ),
            SkillEvidenceGroup(
                skill="Statistics",
                evidence=[
                    EvidenceItem(
                        id=uuid4(), skill="Statistics", source_type="challenge",
                        source_reference=None,
                        observation="Did not apply hypothesis testing to validate the revenue increase",
                        confidence=0.35, created_at=now,
                    ),
                ],
            ),
        ],
    )
