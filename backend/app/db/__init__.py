"""Async Postgres persistence layer (BLUEPRINT.md Section 16).

Every write function here is a best-effort side-write: it no-ops when no
DATABASE_URL is configured (`app.db.pool.is_available()` is False), and
callers wrap each call with `safe_write` so a live database error never
turns a working API response into a 500 — the in-memory/session-passed
contracts these routers already use remain the source of truth for the
response itself.
"""

import logging

logger = logging.getLogger(__name__)


async def safe_write(coro) -> None:
    """Awaits a db write coroutine, logging (not raising) on failure."""
    try:
        await coro
    except Exception:
        logger.exception("Best-effort DB write failed")
