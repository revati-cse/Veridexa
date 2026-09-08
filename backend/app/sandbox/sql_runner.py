"""In-memory SQLite sandbox for candidate SQL submissions.

Per BLUEPRINT.md Section T: candidates only ever run a single read-only
SELECT against data seeded fresh for that challenge, with a hard timeout and
no filesystem/network access. This module has no FastAPI/DB dependency and
takes no Claude call — it is pure, deterministic, and independently testable.
"""

import re
import sqlite3
import threading

from app.schemas.evaluation import SqlExecutionResult
from app.schemas.sandbox import SandboxDataset

DEFAULT_TIMEOUT_SECONDS = 3.0
# Row cap via fetchmany() also short-circuits many runaway queries for free
# (SQLite fetches lazily, so a plain SELECT over an infinite recursive CTE
# stops after this many rows without ever hitting the timer) — but it can't
# help an aggregate like COUNT(*), which must fully materialize before
# returning anything, so the timeout below is still load-bearing.
MAX_ROWS_RETURNED = 1000

# Anything beyond a single read-only SELECT (or WITH ... SELECT) is rejected
# outright — candidates never get write, schema, or pragma access.
_FORBIDDEN_KEYWORDS = re.compile(
    r"\b("
    r"INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|"
    r"ATTACH|DETACH|PRAGMA|VACUUM|REINDEX|EXEC|EXECUTE"
    r")\b",
    re.IGNORECASE,
)
_ALLOWED_START = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)


def _validate_statement(query: str) -> str | None:
    """Returns a rejection reason, or None if `query` is an allowed
    single read-only statement."""
    stripped = query.strip()
    if not stripped:
        return "Empty query."

    body = stripped[:-1] if stripped.endswith(";") else stripped
    if ";" in body:
        return "Only a single SQL statement is allowed."
    if not _ALLOWED_START.match(stripped):
        return "Only SELECT (or WITH ... SELECT) statements are allowed."
    if _FORBIDDEN_KEYWORDS.search(stripped):
        return "Query contains a forbidden keyword — only read-only SELECT queries are allowed."
    return None


def _seed_database(conn: sqlite3.Connection, dataset: SandboxDataset) -> None:
    cursor = conn.cursor()
    for table in dataset.tables:
        columns_sql = ", ".join(f'"{c}"' for c in table.columns)
        cursor.execute(f'CREATE TABLE "{table.name}" ({columns_sql})')
        if table.rows:
            placeholders = ", ".join("?" for _ in table.columns)
            cursor.executemany(f'INSERT INTO "{table.name}" VALUES ({placeholders})', table.rows)


def run_sql(
    query: str,
    dataset: dict,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> SqlExecutionResult:
    """Validates, seeds, and executes `query` against a fresh in-memory
    SQLite database built from `dataset`. Never raises — every failure mode
    (rejected statement, bad dataset, SQL error, timeout) is captured on the
    returned SqlExecutionResult so callers can feed it straight to the
    evaluation prompt as grounding."""
    rejection = _validate_statement(query)
    if rejection:
        return SqlExecutionResult(success=False, rejected_reason=rejection)

    try:
        parsed_dataset = SandboxDataset.model_validate(dataset)
    except Exception as exc:  # noqa: BLE001 - surfaced as a data error, not a crash
        return SqlExecutionResult(success=False, error=f"Invalid challenge dataset: {exc}")

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    timer = threading.Timer(timeout_seconds, conn.interrupt)
    try:
        _seed_database(conn, parsed_dataset)
        cursor = conn.cursor()
        timer.start()
        cursor.execute(query)
        rows = cursor.fetchmany(MAX_ROWS_RETURNED)
        columns = [d[0] for d in cursor.description] if cursor.description else []
        return SqlExecutionResult(
            success=True,
            columns=columns,
            rows=[list(row) for row in rows],
            row_count=len(rows),
        )
    except sqlite3.OperationalError as exc:
        if "interrupted" in str(exc).lower():
            return SqlExecutionResult(success=False, error=f"Query timed out after {timeout_seconds}s.")
        return SqlExecutionResult(success=False, error=str(exc))
    except sqlite3.Error as exc:
        return SqlExecutionResult(success=False, error=str(exc))
    finally:
        timer.cancel()
        conn.close()
