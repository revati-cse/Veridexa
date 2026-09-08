"""evidence_engine service — BLUEPRINT.md Feature 5 / Section L.

Pure function, no AI call, no DB: composes `evidence` rows (matching the
`evidence` table shape) from the candidate's GitHub analysis and submission
history. Claims are deliberately NOT a source here — "documentation is a
claim, code is evidence, performance is stronger evidence" (Section 2) — a
claim can never masquerade as an evidence row. Claims only ever factor into
readiness_engine's claim-alignment bonus, at a capped 10% weight.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.schemas.evaluation import SubmissionRecord
from app.schemas.evidence import EvidenceItem, EvidenceListResponse, SkillEvidenceGroup
from app.schemas.github import GithubAnalyzeResponse


def build_evidence_rows(
    github_evidence: GithubAnalyzeResponse | None,
    submission_history: list[SubmissionRecord],
) -> list[EvidenceItem]:
    rows: list[EvidenceItem] = []
    now = datetime.now(timezone.utc)

    if github_evidence is not None:
        for skill_evidence in github_evidence.skills:
            for observation in skill_evidence.observations:
                rows.append(
                    EvidenceItem(
                        id=uuid4(),
                        skill=skill_evidence.skill,
                        source_type="github",
                        source_reference=github_evidence.repository,
                        observation=observation,
                        confidence=skill_evidence.confidence,
                        created_at=now,
                    )
                )

    for record in submission_history:
        for observation in record.evaluation.evidence:
            rows.append(
                EvidenceItem(
                    id=uuid4(),
                    skill=observation.skill,
                    source_type="submission",
                    source_reference=record.challenge.title,
                    observation=observation.observation,
                    confidence=observation.confidence,
                    created_at=now,
                )
            )

    return rows


def compute_evidence(
    user_id: UUID,
    github_evidence: GithubAnalyzeResponse | None,
    submission_history: list[SubmissionRecord],
) -> EvidenceListResponse:
    rows = build_evidence_rows(github_evidence, submission_history)

    grouped: dict[str, list[EvidenceItem]] = {}
    order: list[str] = []
    for row in rows:
        if row.skill not in grouped:
            grouped[row.skill] = []
            order.append(row.skill)
        grouped[row.skill].append(row)

    return EvidenceListResponse(
        user_id=user_id,
        skills=[SkillEvidenceGroup(skill=skill, evidence=grouped[skill]) for skill in order],
    )
