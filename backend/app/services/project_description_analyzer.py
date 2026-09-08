"""project_description_analyzer service — the evidence path for a candidate
with a real project but no repository to link (BLUEPRINT.md Section I/M's
GitHub evidence pattern, extended to a free-text description). Same
Claude-call shape (GithubAnalysisAIOutput) and the same
retry-once-then-fixture-fallback contract as every other Claude-calling
service (CLAUDE.md "Demo fallback").

Deliberately does NOT reuse github_analyzer.py's `_assess_claim` /
`_build_claims_vs_evidence` verbatim — that module's wording says
"Repository shows evidence...", which would be misleading for text a
candidate typed rather than code Veridexa read. The assessment logic here
is identical in shape, just worded for a description instead of a repo.
"""

import json
import logging
from pathlib import Path

from app.ai.claude_client import AIServiceUnavailable, call_structured
from app.ai.prompts.project_description_prompt import SYSTEM_PROMPT, build_user_prompt
from app.schemas.common import ClaimLevel, EvidenceStrength
from app.schemas.github import ClaimVsEvidenceItem, GithubAnalysisAIOutput, SkillEvidenceItem
from app.schemas.skill import ClaimedSkill

logger = logging.getLogger(__name__)

_FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "demo_project_description_evidence.json"


def _load_fixture_skills() -> list[SkillEvidenceItem]:
    data = json.loads(_FIXTURE_PATH.read_text())
    return GithubAnalysisAIOutput.model_validate(data).skills


def _assess_claim(claim_level: ClaimLevel | None, evidence_strength: EvidenceStrength) -> str:
    if claim_level is None:
        if evidence_strength in ("strong", "moderate"):
            return "The project description shows evidence of this skill, though it wasn't claimed"
        return "No claim and no meaningful evidence in the project description"
    if evidence_strength == "strong":
        return "Strong evidence in the description supports this claim"
    if evidence_strength == "moderate":
        return "Partially supported — verify via a practical challenge"
    return "Claim not yet supported by the project description"


def _build_claims_vs_evidence(
    claimed_skills: list[ClaimedSkill], skills: list[SkillEvidenceItem]
) -> list[ClaimVsEvidenceItem]:
    evidence_by_skill = {s.skill.lower(): s for s in skills}
    seen: set[str] = set()
    rows: list[ClaimVsEvidenceItem] = []

    for claim in claimed_skills:
        key = claim.skill.lower()
        seen.add(key)
        evidence = evidence_by_skill.get(key)
        strength: EvidenceStrength = evidence.evidence_strength if evidence else "none"
        rows.append(
            ClaimVsEvidenceItem(
                skill=claim.skill,
                claim=claim.level,
                repository_evidence=strength,
                assessment=_assess_claim(claim.level, strength),
            )
        )

    for skill in skills:
        key = skill.skill.lower()
        if key in seen:
            continue
        rows.append(
            ClaimVsEvidenceItem(
                skill=skill.skill,
                claim=None,
                repository_evidence=skill.evidence_strength,
                assessment=_assess_claim(None, skill.evidence_strength),
            )
        )

    return rows


async def analyze_description(
    description: str,
    claimed_skills: list[ClaimedSkill],
    required_skills: list[str],
) -> tuple[list[SkillEvidenceItem], list[ClaimVsEvidenceItem], bool]:
    """Returns (skills, claims_vs_evidence, used_ai_fallback). No network
    access beyond the Claude call itself — there's no external resource to
    fail to reach, unlike github_analyzer.py's GithubAccessError path."""
    claimed_skill_names = [c.skill for c in claimed_skills]

    try:
        ai_output = await call_structured(
            system=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(
                claimed_skills=claimed_skill_names,
                required_skills=required_skills,
                description=description,
            ),
            response_model=GithubAnalysisAIOutput,
        )
        skills = ai_output.skills
        used_fallback = False
    except AIServiceUnavailable as exc:
        logger.warning("project_description_analyzer falling back to fixture skills: %s", exc)
        skills = _load_fixture_skills()
        used_fallback = True

    claims_vs_evidence = _build_claims_vs_evidence(claimed_skills, skills)
    return skills, claims_vs_evidence, used_fallback
