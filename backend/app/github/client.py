"""Read-only GitHub REST API client for github_analyzer.py.

BLUEPRINT.md Section I / 18: server-side token only, read-only endpoints
only. No git clone, no code execution — every call here is a plain GET
against the GitHub REST API.
"""

import base64
import logging
import re
from dataclasses import dataclass
from urllib.parse import quote

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
REQUEST_TIMEOUT_SECONDS = 10.0

_REPO_URL_PATTERN = re.compile(r"^https://github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)/?$")


class GithubAccessError(Exception):
    """Repository can't be read (bad URL, not found, private, rate-limited).
    Callers surface this as a clear error rather than fabricating evidence
    for a repository we were never actually able to look at."""


@dataclass(frozen=True)
class RepoRef:
    owner: str
    repo: str


def parse_repo_url(url: str) -> RepoRef:
    match = _REPO_URL_PATTERN.match(url.strip())
    if not match:
        raise GithubAccessError(f"'{url}' is not a valid https://github.com/<owner>/<repo> URL.")
    repo = match.group("repo")
    if repo.endswith(".git"):
        repo = repo[:-4]
    return RepoRef(owner=match.group("owner"), repo=repo)


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


class GithubClient:
    """Async context manager wrapping the handful of GitHub REST endpoints
    the analyzer needs. One instance per analysis request."""

    def __init__(self, timeout: float = REQUEST_TIMEOUT_SECONDS):
        self._client = httpx.AsyncClient(base_url=GITHUB_API_BASE, headers=_headers(), timeout=timeout)

    async def __aenter__(self) -> "GithubClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self._client.aclose()

    async def get_metadata(self, ref: RepoRef) -> dict:
        resp = await self._client.get(f"/repos/{ref.owner}/{ref.repo}")
        self._raise_for_status(resp, ref)
        return resp.json()

    async def get_languages(self, ref: RepoRef) -> dict[str, int]:
        resp = await self._client.get(f"/repos/{ref.owner}/{ref.repo}/languages")
        self._raise_for_status(resp, ref)
        return resp.json()

    async def get_tree(self, ref: RepoRef, branch: str) -> list[dict]:
        # Percent-encode: branch names can legitimately contain "/" (e.g.
        # "release/v1"), and this is a raw f-string URL, not auto-encoded by
        # httpx — an unescaped segment could otherwise be misinterpreted as
        # extra path structure.
        resp = await self._client.get(
            f"/repos/{ref.owner}/{ref.repo}/git/trees/{quote(branch, safe='')}", params={"recursive": "1"}
        )
        self._raise_for_status(resp, ref)
        data = resp.json()
        if data.get("truncated"):
            logger.warning("GitHub tree for %s/%s was truncated by the API itself", ref.owner, ref.repo)
        return [entry for entry in data.get("tree", []) if entry.get("type") == "blob"]

    async def get_file_content(self, ref: RepoRef, path: str) -> str | None:
        """Returns decoded text content, or None if the file is missing, not
        base64-encoded (e.g. a GitHub-side redirect for a huge file), or not
        valid UTF-8 text."""
        # Percent-encode each path segment but keep "/" as the directory
        # separator GitHub expects — paths come from GitHub's own tree
        # listing and can contain spaces or other characters that need
        # escaping in a raw f-string URL.
        resp = await self._client.get(f"/repos/{ref.owner}/{ref.repo}/contents/{quote(path, safe='/')}")
        if resp.status_code == 404:
            return None
        self._raise_for_status(resp, ref)
        data = resp.json()
        if not isinstance(data, dict) or data.get("encoding") != "base64" or "content" not in data:
            return None
        try:
            return base64.b64decode(data["content"]).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None

    def _raise_for_status(self, resp: httpx.Response, ref: RepoRef) -> None:
        if resp.status_code == 404:
            raise GithubAccessError(f"Repository {ref.owner}/{ref.repo} was not found (or is private).")
        if resp.status_code == 403:
            if resp.headers.get("x-ratelimit-remaining") == "0":
                raise GithubAccessError("GitHub API rate limit exceeded — try again shortly.")
            raise GithubAccessError(f"Access to {ref.owner}/{ref.repo} was forbidden by GitHub.")
        if resp.status_code >= 400:
            raise GithubAccessError(f"GitHub API returned {resp.status_code} for {ref.owner}/{ref.repo}.")
