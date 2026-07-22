"""SQLite schema for the Dzongkha Autocorrect foundation.

Every table tracks provenance. ``gold`` is the one table that must never
receive agent- or synthetic-touched data: this is enforced with a CHECK
constraint here (tamper-proof against any writer, including future
migrations or a raw sqlite session) AND, separately, at the repository API
level (dzongkha_autocorrect.db.repository.insert_gold has no ``provenance``
parameter to misuse). See tests/test_gold_provenance.py for both layers.
"""

from __future__ import annotations

import sqlite3

_CREATE_LEXICON = """
CREATE TABLE IF NOT EXISTS lexicon (
    word        TEXT PRIMARY KEY,
    frequency   INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL CHECK (status IN ('valid', 'variant', 'invalid')),
    provenance  TEXT NOT NULL CHECK (provenance IN ('human', 'agent', 'seed')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""

_CREATE_FEEDBACK = """
CREATE TABLE IF NOT EXISTS feedback (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    text_span    TEXT NOT NULL,
    suggestion   TEXT,
    user_action  TEXT NOT NULL CHECK (user_action IN ('accept', 'deny')),
    context      TEXT,
    session_id   TEXT,
    created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    provenance   TEXT NOT NULL DEFAULT 'user' CHECK (provenance = 'user')
);
"""

_CREATE_GOLD = """
CREATE TABLE IF NOT EXISTS gold (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    input            TEXT NOT NULL,
    expected_output  TEXT NOT NULL,
    label_type       TEXT NOT NULL CHECK (label_type IN ('correct', 'wrong', 'variant')),
    provenance       TEXT NOT NULL DEFAULT 'human' CHECK (provenance = 'human'),
    locked           INTEGER NOT NULL DEFAULT 1 CHECK (locked = 1),
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""

_CREATE_REVIEW_QUEUE = """
CREATE TABLE IF NOT EXISTS review_queue (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    item              TEXT NOT NULL,
    agent_guess       TEXT,
    agent_confidence  REAL CHECK (agent_confidence IS NULL OR agent_confidence BETWEEN 0 AND 1),
    human_decision    TEXT CHECK (human_decision IS NULL OR human_decision IN ('accept', 'deny', 'defer')),
    is_gold           INTEGER NOT NULL DEFAULT 0 CHECK (is_gold IN (0, 1)),
    created_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""

# Not in the Phase 0 prompt's literal 4-table list, but required to satisfy
# deliverable #2 ("a corpus loader that ... stores them with a source tag").
_CREATE_CORPUS_DOCUMENTS = """
CREATE TABLE IF NOT EXISTS corpus_documents (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    source             TEXT NOT NULL,
    original_filename  TEXT,
    raw_text           TEXT NOT NULL,
    normalized_text    TEXT NOT NULL,
    ingested_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""

_ALL_DDL = (
    _CREATE_LEXICON,
    _CREATE_FEEDBACK,
    _CREATE_GOLD,
    _CREATE_REVIEW_QUEUE,
    _CREATE_CORPUS_DOCUMENTS,
)


def init_db(conn: sqlite3.Connection) -> None:
    for ddl in _ALL_DDL:
        conn.execute(ddl)
    conn.commit()
