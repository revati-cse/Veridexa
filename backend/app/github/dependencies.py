"""Parses dependency names out of manifest files — BLUEPRINT.md Section I
step 8 "Dependency signal". Pure text parsing, no network, no LLM call.
"""

import json
import re
import tomllib

_VERSION_SPECIFIER_SPLIT = re.compile(r"[=<>!~\[; ]")


def parse_requirements_txt(content: str) -> list[str]:
    names = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        name = _VERSION_SPECIFIER_SPLIT.split(line, maxsplit=1)[0].strip()
        if name:
            names.append(name)
    return names


def parse_package_json(content: str) -> list[str]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []
    names: list[str] = []
    for key in ("dependencies", "devDependencies"):
        deps = data.get(key)
        if isinstance(deps, dict):
            names.extend(deps.keys())
    return names


def parse_pyproject_toml(content: str) -> list[str]:
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError:
        return []

    names: list[str] = []

    # PEP 621: [project] dependencies = ["pandas>=2.0", ...]
    project_deps = data.get("project", {}).get("dependencies", [])
    for dep in project_deps:
        name = _VERSION_SPECIFIER_SPLIT.split(dep, maxsplit=1)[0].strip()
        if name:
            names.append(name)

    # Poetry: [tool.poetry.dependencies]
    poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    if isinstance(poetry_deps, dict):
        names.extend(name for name in poetry_deps if name.lower() != "python")

    return names


_PARSERS = {
    "requirements.txt": parse_requirements_txt,
    "package.json": parse_package_json,
    "pyproject.toml": parse_pyproject_toml,
}


def extract_dependencies(files: dict[str, str]) -> list[str]:
    """`files` maps repo path -> file content, for whatever manifest files
    were fetched. Returns a de-duplicated, order-preserving flat list."""
    names: list[str] = []
    for path, content in files.items():
        parser = _PARSERS.get(path.rsplit("/", 1)[-1])
        if parser:
            names.extend(parser(content))

    seen: set[str] = set()
    deduped = []
    for name in names:
        if name not in seen:
            seen.add(name)
            deduped.append(name)
    return deduped
