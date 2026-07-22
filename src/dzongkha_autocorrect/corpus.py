"""Corpus ingestion: raw .txt files in, normalized + source-tagged rows out.

No correction logic here — this is plumbing only.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from dzongkha_autocorrect.normalize import normalize


def ingest_file(path: str | Path, source: str, conn: sqlite3.Connection) -> int:
    """Read a single .txt file, normalize it, and store it with a source
    tag. Returns the new corpus_documents row id.
    """
    path = Path(path)
    raw_text = path.read_text(encoding="utf-8")
    normalized_text = normalize(raw_text)
    cur = conn.execute(
        """
        INSERT INTO corpus_documents (source, original_filename, raw_text, normalized_text)
        VALUES (?, ?, ?, ?)
        """,
        (source, path.name, raw_text, normalized_text),
    )
    conn.commit()
    return cur.lastrowid


def ingest_directory(
    dir_path: str | Path,
    source: str,
    conn: sqlite3.Connection,
    pattern: str = "*.txt",
) -> list[int]:
    """Ingest every file matching ``pattern`` directly inside ``dir_path``
    (non-recursive). Returns the list of new corpus_documents row ids, in
    the order the files were ingested.
    """
    dir_path = Path(dir_path)
    ids = []
    for file_path in sorted(dir_path.glob(pattern)):
        ids.append(ingest_file(file_path, source, conn))
    return ids
