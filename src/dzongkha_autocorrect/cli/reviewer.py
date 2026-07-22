"""dza-review: the only sanctioned way for a human to populate the gold
table by hand.

`add` and `promote` refuse to run unless stdin is an interactive TTY, so an
agent or script piping input can never auto-populate gold. There is no
--yes/--force flag: every gold row requires a live human confirming in a
real terminal session.
"""

from __future__ import annotations

import argparse
import sys

from dzongkha_autocorrect.db import get_connection, init_db
from dzongkha_autocorrect.db.repository import (
    insert_gold,
    promote_review_item_to_gold,
)
from dzongkha_autocorrect.normalize import normalize
from dzongkha_autocorrect.paths import DEFAULT_DB_PATH

_LABEL_TYPES = ("correct", "wrong", "variant")
_REFUSAL = (
    "Gold entries require an interactive human reviewer session — "
    "refusing to auto-populate gold."
)


def _require_tty() -> None:
    if not sys.stdin.isatty():
        print(_REFUSAL, file=sys.stderr)
        raise SystemExit(1)


def _prompt_label_type() -> str:
    while True:
        value = input(f"label_type {_LABEL_TYPES}: ").strip()
        if value in _LABEL_TYPES:
            return value
        print(f"must be one of {_LABEL_TYPES}")


def cmd_add(args: argparse.Namespace) -> None:
    _require_tty()
    input_text = input("input: ")
    expected_output = input("expected_output: ")
    label_type = _prompt_label_type()

    print("--- normalized preview ---")
    print("input:           ", normalize(input_text))
    print("expected_output: ", normalize(expected_output))
    print("label_type:      ", label_type)
    confirm = input("Add this to gold? [y/N]: ").strip().lower()
    if confirm != "y":
        print("aborted, nothing written")
        return

    conn = get_connection(args.db_path)
    init_db(conn)
    gold_id = insert_gold(conn, input_text, expected_output, label_type)
    print(f"gold row {gold_id} added")


def cmd_promote(args: argparse.Namespace) -> None:
    _require_tty()
    conn = get_connection(args.db_path)
    init_db(conn)

    row = conn.execute(
        "SELECT item, agent_guess, agent_confidence FROM review_queue WHERE id = ?",
        (args.review_queue_id,),
    ).fetchone()
    if row is None:
        print(f"no review_queue row with id {args.review_queue_id}", file=sys.stderr)
        raise SystemExit(1)
    item, agent_guess, agent_confidence = row

    print("--- review_queue item ---")
    print("item:             ", item)
    print("agent_guess:      ", agent_guess)
    print("agent_confidence: ", agent_confidence)

    default = agent_guess or ""
    expected_output = input(f"expected_output [{default}]: ").strip() or default
    label_type = _prompt_label_type()
    human_decision = input("human_decision (accept/deny/defer): ").strip()

    confirm = input("Promote to gold? [y/N]: ").strip().lower()
    if confirm != "y":
        print("aborted, nothing written")
        return

    gold_id = promote_review_item_to_gold(
        conn, args.review_queue_id, expected_output, label_type, human_decision
    )
    print(f"gold row {gold_id} added, review_queue {args.review_queue_id} marked promoted")


def cmd_list(args: argparse.Namespace) -> None:
    conn = get_connection(args.db_path)
    init_db(conn)
    rows = conn.execute(
        "SELECT id, input, expected_output, label_type, created_at "
        "FROM gold ORDER BY id DESC LIMIT ?",
        (args.limit,),
    ).fetchall()
    for row in rows:
        print(row)


def cmd_stats(args: argparse.Namespace) -> None:
    conn = get_connection(args.db_path)
    init_db(conn)
    rows = conn.execute(
        "SELECT label_type, COUNT(*) FROM gold GROUP BY label_type"
    ).fetchall()
    total = sum(count for _, count in rows)
    print(f"total gold rows: {total}")
    for label_type, count in rows:
        print(f"  {label_type}: {count}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dza-review")
    parser.add_argument(
        "--db-path", default=str(DEFAULT_DB_PATH), help="path to the sqlite db"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("add", help="interactively add a gold item").set_defaults(func=cmd_add)

    p_promote = sub.add_parser(
        "promote", help="promote a review_queue item to gold"
    )
    p_promote.add_argument("review_queue_id", type=int)
    p_promote.set_defaults(func=cmd_promote)

    p_list = sub.add_parser("list", help="list recent gold items")
    p_list.add_argument("--limit", type=int, default=20)
    p_list.set_defaults(func=cmd_list)

    sub.add_parser("stats", help="show gold counts by label_type").set_defaults(
        func=cmd_stats
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
