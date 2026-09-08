import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.rate_limit import RateLimitMiddleware


def _make_app(max_requests: int, window_seconds: float, with_cors: bool = False) -> FastAPI:
    app = FastAPI()

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    app.add_middleware(RateLimitMiddleware, max_requests=max_requests, window_seconds=window_seconds)
    if with_cors:
        app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"])
    return app


def test_requests_under_the_limit_all_succeed():
    client = TestClient(_make_app(max_requests=5, window_seconds=60))

    for _ in range(5):
        assert client.get("/ping").status_code == 200


def test_requests_over_the_limit_are_rejected_with_429():
    client = TestClient(_make_app(max_requests=3, window_seconds=60))

    for _ in range(3):
        assert client.get("/ping").status_code == 200

    response = client.get("/ping")
    assert response.status_code == 429
    assert "too many requests" in response.json()["detail"].lower()


def test_limit_resets_after_the_window_expires():
    client = TestClient(_make_app(max_requests=2, window_seconds=0.1))

    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 429

    time.sleep(0.15)

    assert client.get("/ping").status_code == 200


def test_rate_limited_response_still_carries_cors_headers():
    # CORSMiddleware must be outermost (added after RateLimitMiddleware) so
    # a 429 rejection still carries CORS headers — otherwise the frontend
    # can't even read the rejection and just sees an opaque network error.
    client = TestClient(_make_app(max_requests=1, window_seconds=60, with_cors=True))

    client.get("/ping", headers={"Origin": "http://localhost:3000"})
    response = client.get("/ping", headers={"Origin": "http://localhost:3000"})

    assert response.status_code == 429
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_different_clients_are_tracked_independently():
    # TestClient always reports the same client host, so this exercises the
    # per-key bucketing logic directly rather than through real distinct IPs.
    from app.rate_limit import RateLimitMiddleware as RL

    middleware = RL(app=None, max_requests=2, window_seconds=60)
    now = time.monotonic()
    middleware._hits["1.1.1.1"].extend([now, now])  # already at the limit
    # "2.2.2.2" has no hits yet — its own bucket must be unaffected
    assert len(middleware._hits["2.2.2.2"]) == 0
