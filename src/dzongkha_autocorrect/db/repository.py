"""Data-access functions. This is the only sanctioned way to write to the
schema in dzongkha_autocorrect.db.schema.

All text is normalized before it touches the database, per the project's
normalize-before-anything rule.
"""

from __future__ import annotations

import sqlite3

from dzongkha_autocorrect.normalize import normalize

_VALID_LEXICON_STATUS = {"valid", "variant", "invalid"}
_VALID_LEXICON_PROVENANCE = {"human", "agent", "seed"}
_VALID_GOLD_LABEL_TYPE = {"correct", "wrong", "variant"}
_VALID_USER_ACTION = {"accept", "deny"}
_VALID_HUMAN_DECISION = {"accept", "deny", "defer"}


def insert_lexicon(
    conn: sqlite3.Connection,
    word: str,
    frequency: int,
    status: str,
    provenance: str,
) -> None:
    if status not in _VALID_LEXICON_STATUS:
        raise ValueError(f"invalid lexicon status: {status!r}")
    if provenance not in _VALID_LEXICON_PROVENANCE:
        raise ValueError(f"invalid lexicon provenance: {provenance!r}")
    conn.execute(
        """
        INSERT INTO lexicon (word, frequency, status, provenance)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(word) DO UPDATE SET
            frequency = excluded.frequency,
            status = excluded.status,
            provenance = excluded.provenance,
            updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
        """,
        (normalize(word), frequency, status, provenance),
    )
    conn.commit()


def insert_feedback(
    conn: sqlite3.Connection,
    text_span: str,
    suggestion: str | None,
    user_action: str,
    context: str | None = None,
    session_id: str | None = None,
) -> int:
    if user_action not in _VALID_USER_ACTION:
        raise ValueError(f"invalid feedback user_action: {user_action!r}")
    cur = conn.execute(
        """
        INSERT INTO feedback (text_span, suggestion, user_action, context, session_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            normalize(text_span),
            normalize(suggestion) if suggestion is not None else None,
            user_action,
            context,
            session_id,
        ),
    )
    conn.commit()
    return cur.lastrowid


def insert_gold(
    conn: sqlite3.Connection,
    input_text: str,
    expected_output: str,
    label_type: str,
) -> int:
    """The sole path into the gold table. Deliberately takes no
    ``provenance`` parameter: every row this function writes is
    provenance='human' by construction, matching the table's CHECK
    constraint. There is no way to call this function to write a
    non-human-verified gold row.
    """
    if label_type not in _VALID_GOLD_LABEL_TYPE:
        raise ValueError(f"invalid gold label_type: {label_type!r}")
    cur = conn.execute(
        """
        INSERT INTO gold (input, expected_output, label_type, provenance, locked)
        VALUES (?, ?, ?, 'human', 1)
        """,
        (normalize(input_text), normalize(expected_output), label_type),
    )
    conn.commit()
    return cur.lastrowid


def insert_review_queue(
    conn: sqlite3.Connection,
    item: str,
    agent_guess: str | None = None,
    agent_confidence: float | None = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO review_queue (item, agent_guess, agent_confidence)
        VALUES (?, ?, ?)
        """,
        (
            normalize(item),
            normalize(agent_guess) if agent_guess is not None else None,
            agent_confidence,
        ),
    )
    conn.commit()
    return cur.lastrowid


def promote_review_item_to_gold(
    conn: sqlite3.Connection,
    review_queue_id: int,
    expected_output: str,
    label_type: str,
    human_decision: str,
) -> int:
    """Record a reviewer's decision on a queued item and, for an
    'accept', write the human-confirmed result to gold via insert_gold
    (never a direct write of agent_guess/agent_confidence to gold).
    """
    if human_decision not in _VALID_HUMAN_DECISION:
        raise ValueError(f"invalid human_decision: {human_decision!r}")
    row = conn.execute(
        "SELECT item FROM review_queue WHERE id = ?", (review_queue_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"no review_queue row with id {review_queue_id!r}")
    item_text = row[0]

    gold_id = insert_gold(conn, item_text, expected_output, label_type)

    conn.execute(
        "UPDATE review_queue SET human_decision = ?, is_gold = 1 WHERE id = ?",
        (human_decision, review_queue_id),
    )
    conn.commit()
    return gold_id
