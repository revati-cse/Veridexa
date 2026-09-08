"""Async Postgres connection pool — BLUEPRINT.md Section 16.

Wraps asyncpg directly against DATABASE_URL (Supabase exposes a standard
Postgres connection string) rather than a heavier ORM — "do not introduce
complex infrastructure" (Section 23). Every persistence call site checks
is_available() first and degrades gracefully — matching the
AIServiceUnavailable pattern already used for Claude/GitHub — rather than
crashing when no DATABASE_URL is configured. The app runs and demos
correctly with or without a database wired up.
"""

import json
import logging

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


class DatabaseUnavailable(Exception):
    """Raised only by code that requires a connection and calls acquire()
    directly without checking is_available() first — persistence call
    sites should check is_available() and skip instead of hitting this."""


async def _init_connection(conn: asyncpg.Connection) -> None:
    # jsonb columns round-trip as native Python dicts/lists instead of raw
    # JSON strings — every persistence module relies on this codec being
    # registered rather than hand-rolling json.dumps/loads per query.
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


async def connect() -> None:
    global _pool
    if not settings.database_url:
        logger.warning("DATABASE_URL not configured — running without persistence.")
        return
    _pool = await asyncpg.create_pool(
        settings.database_url, min_size=1, max_size=5, init=_init_connection
    )
    logger.info("Database connection pool established.")


async def disconnect() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def is_available() -> bool:
    return _pool is not None


def acquire():
    """Async context manager yielding a pooled connection. Callers should
    check is_available() first — this raises DatabaseUnavailable rather
    than hanging or crashing obscurely if called with no pool configured."""
    if _pool is None:
        raise DatabaseUnavailable("No database connection configured.")
    return _pool.acquire()
