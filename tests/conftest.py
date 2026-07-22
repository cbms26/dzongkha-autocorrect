from __future__ import annotations

import pytest

from dzongkha_autocorrect.db import get_connection, init_db


@pytest.fixture
def tmp_db(tmp_path):
    conn = get_connection(tmp_path / "test.db")
    init_db(conn)
    yield conn
    conn.close()
