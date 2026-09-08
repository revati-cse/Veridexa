from app.sandbox.sql_runner import run_sql

DATASET = {
    "tables": [
        {
            "name": "customers",
            "columns": ["id", "name"],
            "rows": [[1, "Alice"], [2, "Bob"]],
        },
        {
            "name": "orders",
            "columns": ["id", "customer_id", "amount"],
            "rows": [[1, 1, 100], [2, 1, 50], [3, 2, 75]],
        },
    ]
}


def test_valid_select_with_join_and_group_by_returns_rows():
    query = """
        SELECT c.name, SUM(o.amount) AS total
        FROM customers c JOIN orders o ON o.customer_id = c.id
        GROUP BY c.name
        ORDER BY c.name
    """
    result = run_sql(query, DATASET)

    assert result.success is True
    assert result.error is None
    assert result.columns == ["name", "total"]
    assert result.rows == [["Alice", 150], ["Bob", 75]]
    assert result.row_count == 2


def test_valid_select_with_cte_is_allowed():
    query = "WITH totals AS (SELECT customer_id, SUM(amount) AS total FROM orders GROUP BY customer_id) SELECT * FROM totals"
    result = run_sql(query, DATASET)

    assert result.success is True
    assert result.row_count == 2


def test_empty_query_is_rejected():
    result = run_sql("", DATASET)

    assert result.success is False
    assert result.rejected_reason == "Empty query."


def test_write_statements_are_rejected():
    for query in [
        "INSERT INTO customers VALUES (3, 'Eve')",
        "UPDATE customers SET name = 'x' WHERE id = 1",
        "DELETE FROM customers",
        "DROP TABLE customers",
        "CREATE TABLE evil (id INTEGER)",
        "ATTACH DATABASE 'x.db' AS x",
        "PRAGMA table_info(customers)",
    ]:
        result = run_sql(query, DATASET)
        assert result.success is False, query
        assert result.rejected_reason is not None, query


def test_pragma_table_valued_functions_are_rejected():
    # SQLite exposes pragmas as callable table-valued functions too —
    # `SELECT * FROM pragma_table_info(...)` contains no standalone "PRAGMA"
    # word, so a naive \bPRAGMA\b denylist would let it through even though
    # it's real pragma access. Confirmed via direct sqlite3 experimentation
    # before fixing: pragma_table_info('t') and pragma_database_list both
    # execute successfully against a bare in-memory connection.
    for query in [
        "SELECT * FROM pragma_table_info('customers')",
        "SELECT * FROM pragma_database_list",
        "select * from PRAGMA_compile_options",
    ]:
        result = run_sql(query, DATASET)
        assert result.success is False, query
        assert result.rejected_reason is not None, query


def test_load_extension_is_rejected_by_denylist_and_also_blocked_by_sqlite_itself():
    # Belt-and-suspenders: Python's sqlite3 module blocks load_extension by
    # default (no enable_load_extension() call is ever made here), but the
    # denylist should catch it too rather than relying solely on that
    # runtime default, which is a config detail, not a guarantee.
    result = run_sql("SELECT load_extension('whatever')", DATASET)

    assert result.success is False
    assert result.rejected_reason is not None


def test_multiple_statements_are_rejected():
    result = run_sql("SELECT * FROM customers; DROP TABLE customers;", DATASET)

    assert result.success is False
    assert result.rejected_reason == "Only a single SQL statement is allowed."


def test_trailing_semicolon_alone_is_still_allowed():
    result = run_sql("SELECT * FROM customers;", DATASET)

    assert result.success is True
    assert result.row_count == 2


def test_invalid_dataset_identifier_is_rejected():
    bad_dataset = {"tables": [{"name": "bad; drop", "columns": ["id"], "rows": []}]}
    result = run_sql("SELECT * FROM customers", bad_dataset)

    assert result.success is False
    assert "Invalid challenge dataset" in result.error


def test_oversized_dataset_is_rejected_not_seeded():
    # Legitimate datasets are 5-15 rows (per the challenge-generation
    # prompts) — a raw API caller sending something wildly larger (bypassing
    # the UI, which never lets a candidate edit the dataset directly) should
    # be rejected as a bad dataset, not silently seeded into memory.
    huge_dataset = {
        "tables": [{"name": "customers", "columns": ["id"], "rows": [[i] for i in range(100_000)]}]
    }
    result = run_sql("SELECT * FROM customers", huge_dataset)

    assert result.success is False
    assert "Invalid challenge dataset" in result.error


def test_too_many_tables_is_rejected():
    huge_dataset = {
        "tables": [{"name": f"t{i}", "columns": ["id"], "rows": []} for i in range(1000)]
    }
    result = run_sql("SELECT 1", huge_dataset)

    assert result.success is False
    assert "Invalid challenge dataset" in result.error


def test_query_against_nonexistent_table_reports_sql_error():
    result = run_sql("SELECT * FROM does_not_exist", DATASET)

    assert result.success is False
    assert result.rejected_reason is None
    assert "no such table" in result.error.lower()


def test_long_running_query_times_out():
    # COUNT(*) must fully materialize the recursion before returning a single
    # row, so — unlike a plain SELECT — it can't be short-circuited by the
    # MAX_ROWS_RETURNED cap via lazy fetch; this genuinely exercises the timer.
    infinite_recursion_count = (
        "WITH RECURSIVE cnt(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM cnt) "
        "SELECT COUNT(*) FROM cnt"
    )
    result = run_sql(infinite_recursion_count, {"tables": []}, timeout_seconds=0.2)

    assert result.success is False
    assert result.rejected_reason is None
    assert "timed out" in result.error.lower()


def test_row_count_is_capped():
    big_dataset = {
        "tables": [
            {
                "name": "numbers",
                "columns": ["n"],
                "rows": [[i] for i in range(2000)],
            }
        ]
    }
    result = run_sql("SELECT * FROM numbers", big_dataset)

    assert result.success is True
    assert result.row_count == 1000
