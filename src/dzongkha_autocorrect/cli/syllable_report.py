"""dza-syllable-report: read-only reviewer-report generator for the Phase 1
syllable validator.

Prints up to 50 flagged (structurally-invalid) syllables from a text
source, in a plain syllable/reason/confirm-deny-blank format for a
Dzongkha speaker to work through in one pass. This command writes nothing
-- no gold, no review_queue, no lexicon, no correction logic. Turning a
speaker's "actually valid" answer into a gold row remains dza-review
add's job (dzongkha_autocorrect.cli.reviewer), not duplicated here.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from dzongkha_autocorrect.db import get_connection, init_db
from dzongkha_autocorrect.paths import DEFAULT_DB_PATH
from dzongkha_autocorrect.rules.syllable import FlaggedSpan, check_text

_DEFAULT_SAMPLE_SIZE = 50


def _load_text_from_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _load_text_from_corpus(db_path: str) -> str:
    """Read-only: opens the db to SELECT from corpus_documents. init_db is
    idempotent (CREATE TABLE IF NOT EXISTS) so this never writes rows.
    """
    conn = get_connection(db_path)
    init_db(conn)
    rows = conn.execute("SELECT normalized_text FROM corpus_documents").fetchall()
    conn.close()
    return "\n".join(row[0] for row in rows)


def _sample(
    flagged: list[FlaggedSpan], sample_size: int, seed: int | None
) -> list[FlaggedSpan]:
    if len(flagged) <= sample_size:
        return flagged
    rng = random.Random(seed)
    return rng.sample(flagged, sample_size)


def format_report(flagged_sample: list[FlaggedSpan]) -> str:
    lines = [f"{len(flagged_sample)} flagged syllable(s) for review", ""]
    for i, item in enumerate(flagged_sample, start=1):
        lines.append(f"[{i}] syllable: {item['span']}")
        lines.append(f"    reason:   {item['reason']}")
        lines.append("    actually valid Dzongkha? confirm/deny [y/n]: ____")
        lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dza-syllable-report",
        description=(
            "Read-only report of syllables the Phase 1 validator flags as "
            "structurally invalid, for a Dzongkha speaker to confirm/deny. "
            "Writes nothing to the database."
        ),
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="path to a raw .txt file to check")
    source.add_argument(
        "--from-corpus",
        action="store_true",
        help="check all text already ingested into corpus_documents",
    )
    parser.add_argument(
        "--db-path",
        default=str(DEFAULT_DB_PATH),
        help="path to the sqlite db (only used with --from-corpus)",
    )
    parser.add_argument("--sample-size", type=int, default=_DEFAULT_SAMPLE_SIZE)
    parser.add_argument(
        "--seed", type=int, default=None, help="random seed for reproducible sampling"
    )
    parser.add_argument(
        "--output", help="write the report to this file instead of stdout"
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    text = (
        _load_text_from_file(args.input)
        if args.input
        else _load_text_from_corpus(args.db_path)
    )

    flagged = check_text(text)
    sample = _sample(flagged, args.sample_size, args.seed)
    report = format_report(sample)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    else:
        # Tibetan-script output needs a UTF-8 stream regardless of the
        # host console's default code page.
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(report + "\n")


if __name__ == "__main__":
    main()
