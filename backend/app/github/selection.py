"""Ranks a repository's file tree and picks the bounded subset actually sent
to Claude — BLUEPRINT.md Section I "Source file selection strategy".

Deliberately simple: an extension -> skill-name hint table plus a few cheap
heuristics (depth, test-directory de-prioritization, size sweet-spot). No
per-file network calls happen here — this only scores tree metadata already
fetched by GithubClient.get_tree().
"""

from app.github.filters import (
    DEPENDENCY_FILENAMES,
    MAX_FILE_SIZE_BYTES,
    MAX_TREE_ENTRIES,
    MIN_FILE_SIZE_BYTES,
    SOURCE_EXTENSIONS,
    extension_of,
    is_excluded,
)

DEFAULT_LIMIT = 15
MAX_DEPENDENCY_FILES = 3

_TEST_DIR_NAMES = {"test", "tests", "__tests__", "spec", "specs"}

# Best-effort extension -> lowercase skill-name hints, used only to rank
# files that are relevant to the candidate's claimed/required skills higher
# — not an authoritative skill taxonomy.
_EXTENSION_SKILL_HINTS: dict[str, set[str]] = {
    ".py": {"python"},
    ".sql": {"sql"},
    ".js": {"javascript"},
    ".jsx": {"javascript", "react"},
    ".ts": {"typescript"},
    ".tsx": {"typescript", "react"},
    ".java": {"java"},
    ".go": {"go"},
    ".r": {"r"},
    ".rb": {"ruby"},
    ".php": {"php"},
    ".cs": {"c#"},
    ".cpp": {"c++"},
    ".c": {"c"},
    ".kt": {"kotlin"},
    ".scala": {"scala"},
    ".swift": {"swift"},
    ".ipynb": {"python", "machine learning", "data analysis"},
}


def _relevance_score(path: str, size: int, relevant_skills: set[str]) -> float:
    ext = extension_of(path)
    score = 0.0

    hints = _EXTENSION_SKILL_HINTS.get(ext, set())
    if hints & relevant_skills:
        score += 5.0
    elif ext in SOURCE_EXTENSIONS:
        score += 1.0  # still source code, just not directly claimed/required

    segments = path.split("/")
    score -= (len(segments) - 1) * 0.3  # prefer shallower / more central files
    if any(segment.lower() in _TEST_DIR_NAMES for segment in segments[:-1]):
        score -= 1.0  # de-prioritize, don't exclude outright — tests are still evidence
    if len(segments) == 1 or segments[0] == "src":
        score += 0.5

    if size < MIN_FILE_SIZE_BYTES or size > MAX_FILE_SIZE_BYTES:
        score -= 3.0  # empty stubs or huge generated dumps

    return score


def select_files_for_analysis(
    tree_entries: list[dict],
    claimed_skills: list[str],
    required_skills: list[str],
    limit: int = DEFAULT_LIMIT,
) -> tuple[list[dict], list[dict]]:
    """Returns (source_files, dependency_files), both capped and sorted most-
    relevant first. Dependency manifests (requirements.txt etc.) are always
    considered separately from the scored source-file ranking, since their
    value is the dependency list, not their content as "code"."""
    tree_entries = tree_entries[:MAX_TREE_ENTRIES]
    relevant_skills = {s.lower() for s in [*claimed_skills, *required_skills]}

    dependency_candidates = [
        entry
        for entry in tree_entries
        if not is_excluded(entry["path"]) and entry["path"].rsplit("/", 1)[-1] in DEPENDENCY_FILENAMES
    ]
    dependency_candidates.sort(key=lambda entry: entry["path"].count("/"))
    dependency_files = dependency_candidates[:MAX_DEPENDENCY_FILES]
    dependency_paths = {entry["path"] for entry in dependency_files}

    scored_source: list[tuple[float, dict]] = []
    for entry in tree_entries:
        path = entry["path"]
        if path in dependency_paths or is_excluded(path):
            continue
        if extension_of(path) not in SOURCE_EXTENSIONS:
            continue
        score = _relevance_score(path, entry.get("size", 0), relevant_skills)
        scored_source.append((score, entry))

    scored_source.sort(key=lambda pair: pair[0], reverse=True)
    source_files = [entry for _, entry in scored_source[:limit]]

    return source_files, dependency_files
