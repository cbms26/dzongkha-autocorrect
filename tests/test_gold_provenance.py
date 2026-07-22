"""Both provenance-enforcement layers must independently reject
non-human gold data: the DB CHECK constraint (schema.py) and the
repository API shape (repository.insert_gold has no provenance param).
"""

import sqlite3

import pytest

from dzongkha_autocorrect.db.repository import insert_gold


def test_check_constraint_rejects_non_human_provenance_via_direct_sql(tmp_db):
    with pytest.raises(sqlite3.IntegrityError):
        tmp_db.execute(
            "INSERT INTO gold (input, expected_output, label_type, provenance) "
            "VALUES (?, ?, ?, ?)",
            ("input", "output", "correct", "agent"),
        )


def test_check_constraint_rejects_locked_false(tmp_db):
    with pytest.raises(sqlite3.IntegrityError):
        tmp_db.execute(
            "INSERT INTO gold (input, expected_output, label_type, locked) "
            "VALUES (?, ?, ?, ?)",
            ("input", "output", "correct", 0),
        )


def test_insert_gold_has_no_provenance_parameter(tmp_db):
    with pytest.raises(TypeError):
        insert_gold(  # type: ignore[call-arg]
            tmp_db, "input", "output", "correct", provenance="agent"
        )


def test_insert_gold_writes_human_provenance(tmp_db):
    gold_id = insert_gold(tmp_db, "input", "output", "correct")
    row = tmp_db.execute(
        "SELECT provenance, locked FROM gold WHERE id = ?", (gold_id,)
    ).fetchone()
    assert row == ("human", 1)


def test_insert_gold_rejects_invalid_label_type(tmp_db):
    with pytest.raises(ValueError):
        insert_gold(tmp_db, "input", "output", "not-a-real-label-type")


def test_insert_gold_normalizes_text(tmp_db):
    precomposed = chr(0xF73)  # deprecated VOWEL SIGN II
    decomposed = chr(0xF71) + chr(0xF72)
    gold_id = insert_gold(tmp_db, precomposed, precomposed, "correct")
    row = tmp_db.execute(
        "SELECT input, expected_output FROM gold WHERE id = ?", (gold_id,)
    ).fetchone()
    assert row == (decomposed, decomposed)
