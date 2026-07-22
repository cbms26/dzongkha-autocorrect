from dzongkha_autocorrect.db import get_connection, init_db

EXPECTED_TABLES = {"lexicon", "feedback", "gold", "review_queue", "corpus_documents"}


def test_init_db_creates_all_tables(tmp_db):
    tables = {
        row[0]
        for row in tmp_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert EXPECTED_TABLES <= tables


def test_init_db_is_idempotent(tmp_path):
    conn = get_connection(tmp_path / "test.db")
    init_db(conn)
    init_db(conn)  # must not raise
    conn.close()
