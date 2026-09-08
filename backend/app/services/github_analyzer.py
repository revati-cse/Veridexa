"""github_analyzer service — BLUEPRINT.md Feature 5A / Section I.

Read-only pipeline: validate URL -> fetch metadata/languages/tree -> filter
-> rank & select relevant source files -> fetch bounded content -> parse
dependency signal -> one bounded Claude call for skill evidence -> combine
with the candidate's claims via a deterministic backend rule (Section M —
the LLM never writes the claim-vs-evidence verdict itself).

Repository access failures (bad URL, 404, private, rate-limited) raise
GithubAccessError and propagate to the caller — we never fabricate evidence
for a repository we were never able to read. A Claude-side failure, by
contrast, falls back to a fixture (BLUEPRINT.md Section W), since the repo
data itself was already fetched successfully.
"""

import json
import logging
from pathlib import Path

from app.ai.claude_client import AIServiceUnavailable, call_structured
from app.ai.prompts.github_analysis_prompt import SYSTEM_PROMPT, build_user_prompt
from app.github.client import GithubAccessError, GithubClient, parse_repo_url
from app.github.dependencies import extract_dependencies
from app.github.selection import select_files_for_analysis
from app.schemas.common import ClaimLevel, EvidenceStrength
from app.schemas.github import (
    ClaimVsEvidenceItem,
    GithubAnalysisAIOutput,
    LanguageDetected,
    SkillEvidenceItem,
)
from app.schemas.skill import ClaimedSkill

logger = logging.getLogger(__name__)

_FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "demo_github_evidence.json"

MAX_FILE_LINES = 200
MAX_FILE_CHARS = 6000
MAX_TOTAL_CONTENT_CHARS = 18_000


def _truncate_file(content: str) -> str:
    lines = content.splitlines()[:MAX_FILE_LINES]
    text = "\n".join(lines)
    return text[:MAX_FILE_CHARS]


def _load_fixture_skills() -> list[SkillEvidenceItem]:
    data = json.loads(_FIXTURE_PATH.read_text())
    return GithubAnalysisAIOutput.model_validate(data).skills


def _assess_claim(claim_level: ClaimLevel | None, evidence_strength: EvidenceStrength) -> str:
    if claim_level is None:
        if evidence_strength in ("strong", "moderate"):
            return "Repository shows evidence of this skill, though it wasn't claimed"
        return "No claim and no meaningful repository evidence"
    if evidence_strength == "strong":
        return "Strong evidence supports this claim"
    if evidence_strength == "moderate":
        return "Partially supported — verify via a practical challenge"
    return "Claim not yet supported by repository evidence"


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


async def analyze_repository(
    repository_url: str,
    claimed_skills: list[ClaimedSkill],
    required_skills: list[str],
) -> tuple[list[LanguageDetected], list[SkillEvidenceItem], list[ClaimVsEvidenceItem], bool]:
    """Returns (languages_detected, skills, claims_vs_evidence, used_ai_fallback).

    Raises GithubAccessError if the repository itself can't be read — that
    is not caught here, callers (the router) turn it into a 4xx response.
    """
    ref = parse_repo_url(repository_url)
    claimed_skill_names = [c.skill for c in claimed_skills]

    async with GithubClient() as client:
        metadata = await client.get_metadata(ref)
        languages_raw = await client.get_languages(ref)
        default_branch = metadata.get("default_branch") or "main"
        tree_entries = await client.get_tree(ref, default_branch)

        source_files, dependency_files = select_files_for_analysis(
            tree_entries, claimed_skill_names, required_skills
        )

        contents: dict[str, str] = {}
        total_chars = 0
        for entry in [*dependency_files, *source_files]:
            content = await client.get_file_content(ref, entry["path"])
            if content is None:
                continue
            truncated = _truncate_file(content)
            if total_chars + len(truncated) > MAX_TOTAL_CONTENT_CHARS:
                continue  # drop remaining lowest-ranked files once the token cap is hit
            contents[entry["path"]] = truncated
            total_chars += len(truncated)

    dependency_names = extract_dependencies(contents)
    source_only_contents = {path: text for path, text in contents.items() if path not in {e["path"] for e in dependency_files}}

    total_bytes = sum(languages_raw.values()) or 1
    languages_detected = [
        LanguageDetected(language=lang, confidence=round(byte_count / total_bytes, 2))
        for lang, byte_count in sorted(languages_raw.items(), key=lambda kv: kv[1], reverse=True)
    ]

    try:
        ai_output = await call_structured(
            system=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(
                claimed_skills=claimed_skill_names,
                required_skills=required_skills,
                dependency_names=dependency_names,
                files=source_only_contents,
            ),
            response_model=GithubAnalysisAIOutput,
        )
        skills = ai_output.skills
        used_fallback = False
    except AIServiceUnavailable as exc:
        logger.warning("github_analyzer falling back to fixture skills: %s", exc)
        skills = _load_fixture_skills()
        used_fallback = True

    claims_vs_evidence = _build_claims_vs_evidence(claimed_skills, skills)
    return languages_detected, skills, claims_vs_evidence, used_fallback
