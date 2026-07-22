from dzongkha_autocorrect.db.repository import (
    insert_feedback,
    insert_lexicon,
    insert_review_queue,
    promote_review_item_to_gold,
)
from dzongkha_autocorrect.normalize import normalize


def test_insert_lexicon_inserts_new_word(tmp_db):
    word = chr(0xF73)  # deprecated precomposed form, must be stored normalized
    insert_lexicon(tmp_db, word, frequency=5, status="valid", provenance="seed")
    row = tmp_db.execute(
        "SELECT word, frequency, status, provenance FROM lexicon WHERE word = ?",
        (normalize(word),),
    ).fetchone()
    assert row == (normalize(word), 5, "valid", "seed")


def test_insert_lexicon_upserts_on_conflict(tmp_db):
    word = "word"
    insert_lexicon(tmp_db, word, frequency=1, status="valid", provenance="seed")
    insert_lexicon(tmp_db, word, frequency=9, status="variant", provenance="human")

    rows = tmp_db.execute("SELECT frequency, status, provenance FROM lexicon WHERE word = ?", (word,)).fetchall()
    assert rows == [(9, "variant", "human")]


def test_insert_lexicon_rejects_invalid_status(tmp_db):
    import pytest

    with pytest.raises(ValueError):
        insert_lexicon(tmp_db, "word", frequency=1, status="not-a-status", provenance="seed")


def test_insert_feedback_stores_normalized_span_and_suggestion(tmp_db):
    span = chr(0xF73)
    suggestion = chr(0xF81)
    feedback_id = insert_feedback(
        tmp_db, span, suggestion, "accept", context="ctx", session_id="s1"
    )
    row = tmp_db.execute(
        "SELECT text_span, suggestion, user_action, context, session_id, provenance "
        "FROM feedback WHERE id = ?",
        (feedback_id,),
    ).fetchone()
    assert row == (
        normalize(span),
        normalize(suggestion),
        "accept",
        "ctx",
        "s1",
        "user",
    )


def test_insert_feedback_rejects_invalid_user_action(tmp_db):
    import pytest

    with pytest.raises(ValueError):
        insert_feedback(tmp_db, "span", None, "maybe")


def test_insert_review_queue_stores_normalized_item_and_guess(tmp_db):
    item = chr(0xF73)
    guess = chr(0xF81)
    rq_id = insert_review_queue(tmp_db, item, agent_guess=guess, agent_confidence=0.5)
    row = tmp_db.execute(
        "SELECT item, agent_guess, agent_confidence, human_decision, is_gold "
        "FROM review_queue WHERE id = ?",
        (rq_id,),
    ).fetchone()
    assert row == (normalize(item), normalize(guess), 0.5, None, 0)


def test_promote_review_item_to_gold_writes_gold_and_marks_queue(tmp_db):
    rq_id = insert_review_queue(tmp_db, "item text", agent_guess="agent guess", agent_confidence=0.8)

    gold_id = promote_review_item_to_gold(
        tmp_db,
        review_queue_id=rq_id,
        expected_output="human-confirmed output",
        label_type="correct",
        human_decision="accept",
    )

    gold_row = tmp_db.execute(
        "SELECT input, expected_output, label_type, provenance FROM gold WHERE id = ?",
        (gold_id,),
    ).fetchone()
    assert gold_row == (
        normalize("item text"),
        normalize("human-confirmed output"),
        "correct",
        "human",
    )

    queue_row = tmp_db.execute(
        "SELECT human_decision, is_gold FROM review_queue WHERE id = ?", (rq_id,)
    ).fetchone()
    assert queue_row == ("accept", 1)


def test_promote_review_item_to_gold_never_copies_agent_guess_verbatim(tmp_db):
    """The promoted gold row's expected_output must come from the human's
    input to promote(), not silently from agent_guess/agent_confidence."""
    rq_id = insert_review_queue(tmp_db, "item text", agent_guess="agent guess", agent_confidence=0.8)

    gold_id = promote_review_item_to_gold(
        tmp_db,
        review_queue_id=rq_id,
        expected_output="a different human decision",
        label_type="wrong",
        human_decision="deny",
    )

    gold_row = tmp_db.execute(
        "SELECT expected_output FROM gold WHERE id = ?", (gold_id,)
    ).fetchone()
    assert gold_row == (normalize("a different human decision"),)


def test_promote_review_item_to_gold_rejects_unknown_review_queue_id(tmp_db):
    import pytest

    with pytest.raises(ValueError):
        promote_review_item_to_gold(
            tmp_db,
            review_queue_id=9999,
            expected_output="x",
            label_type="correct",
            human_decision="accept",
        )
