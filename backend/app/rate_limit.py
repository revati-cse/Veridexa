"""Lightweight in-process rate limiter — BLUEPRINT.md Section T: "Rate-limit
outbound calls per candidate session (basic in-memory counter is enough) to
avoid one demo user burning the Claude/GitHub quota."

Per-process, in-memory, fixed-window-with-eviction, keyed by client IP —
resets on restart and doesn't coordinate across multiple worker processes.
That's an accepted hackathon-scope tradeoff (Section 23: "do not introduce
complex infrastructure"), not a production-grade limiter.

The default (30 requests/60s) is sized for one candidate clicking through
the demo flow, not multi-tenant fairness — if several people demo from the
same shared network (e.g. judges on venue WiFi) and collide on one IP, they
share a single bucket. Raise DEFAULT_MAX_REQUESTS if that happens during
the actual event rather than during development.
"""

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

DEFAULT_MAX_REQUESTS = 30
DEFAULT_WINDOW_SECONDS = 60.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        window_seconds: float = DEFAULT_WINDOW_SECONDS,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client_key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        hits = self._hits[client_key]

        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()

        if len(hits) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests — please wait a moment and try again."},
            )

        hits.append(now)
        return await call_next(request)
