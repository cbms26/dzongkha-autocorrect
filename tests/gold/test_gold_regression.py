"""Regression tests over the live, human-populated gold table.

Reads dzongkha_autocorrect.paths.DEFAULT_DB_PATH (overridable via
DZA_GOLD_DB_PATH), not a static fixture copy, so this suite grows
automatically as a reviewer adds real rows via `dza-review add`/`promote`.

There is no correct() API yet (Phase 0), so the only assertions possible
right now are gold-data integrity ones. Once correct() exists:
    # TODO(Phase 1+): assert correct(row.input) == row.expected_output
"""

import os
from pathlib import Path

from dzongkha_autocorrect.db import get_connection, init_db
from dzongkha_autocorrect.normalize import normalize
from dzongkha_autocorrect.paths import DEFAULT_DB_PATH


def _gold_db_path() -> Path:
    return Path(os.environ.get("DZA_GOLD_DB_PATH", str(DEFAULT_DB_PATH)))


def _load_gold_rows():
    path = _gold_db_path()
    conn = get_connection(path)
    init_db(conn)
    rows = conn.execute(
        "SELECT id, input, expected_output, label_type FROM gold ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


def pytest_generate_tests(metafunc):
    if "gold_row" in metafunc.fixturenames:
        rows = _load_gold_rows()
        metafunc.parametrize("gold_row", rows, ids=[f"gold-{row[0]}" for row in rows])


def test_gold_row_is_normalized_and_valid(gold_row):
    _id, input_text, expected_output, label_type = gold_row
    assert normalize(input_text) == input_text
    assert normalize(expected_output) == expected_output
    assert label_type in ("correct", "wrong", "variant")


def test_gold_table_exists_and_is_queryable():
    """Static placeholder so this file always reports at least one test,
    even when gold is empty (true at Phase 0 completion) and the
    parametrized test above yields zero cases."""
    conn = get_connection(_gold_db_path())
    init_db(conn)
    conn.execute("SELECT COUNT(*) FROM gold").fetchone()
    conn.close()
