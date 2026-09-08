"""GithubClient tests using httpx.MockTransport to inspect the actual
outgoing request URL — the encoding fix (branch/path segments containing
"/" or spaces) can only be verified against the real request, not a mock
of GithubClient itself."""

import asyncio
import base64
import json

import httpx

from app.github.client import GithubClient, RepoRef


def _client_with_transport(handler) -> GithubClient:
    client = GithubClient()
    client._client = httpx.AsyncClient(
        base_url="https://api.github.com", transport=httpx.MockTransport(handler)
    )
    return client


def test_branch_with_slash_is_fully_percent_encoded_in_tree_url():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"tree": [], "truncated": False})

    client = _client_with_transport(handler)
    ref = RepoRef(owner="example", repo="repo")
    asyncio.run(client.get_tree(ref, "release/v1"))

    # The whole branch segment must be one escaped token — a literal "/"
    # here would be interpreted by GitHub as extra path structure.
    assert "/git/trees/release%2Fv1" in captured["url"]
    assert "/git/trees/release/v1" not in captured["url"]


def test_file_path_with_space_is_percent_encoded_but_slashes_kept_as_separators():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        content = base64.b64encode(b"print('hi')").decode()
        return httpx.Response(200, json={"encoding": "base64", "content": content})

    client = _client_with_transport(handler)
    ref = RepoRef(owner="example", repo="repo")
    asyncio.run(client.get_file_content(ref, "src/my file.py"))

    assert "/contents/src/my%20file.py" in captured["url"]


def test_normal_branch_and_path_are_unaffected():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"tree": [], "truncated": False})

    client = _client_with_transport(handler)
    ref = RepoRef(owner="example", repo="repo")
    asyncio.run(client.get_tree(ref, "main"))

    assert "/git/trees/main" in captured["url"]
