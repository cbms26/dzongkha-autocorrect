from pathlib import Path

from dzongkha_autocorrect.corpus import ingest_directory, ingest_file
from dzongkha_autocorrect.normalize import normalize

SAMPLE_DIR = Path(__file__).parent / "data" / "sample_raw"


def test_ingest_file_stores_normalized_text_with_source_tag(tmp_db):
    sample = SAMPLE_DIR / "sample_a.txt"
    row_id = ingest_file(sample, source="unit-test", conn=tmp_db)

    row = tmp_db.execute(
        "SELECT source, original_filename, raw_text, normalized_text "
        "FROM corpus_documents WHERE id = ?",
        (row_id,),
    ).fetchone()
    source, original_filename, raw_text, normalized_text = row
    assert source == "unit-test"
    assert original_filename == "sample_a.txt"
    assert normalized_text == normalize(raw_text)


def test_ingest_directory_ingests_all_matching_files(tmp_db):
    ids = ingest_directory(SAMPLE_DIR, source="unit-test", conn=tmp_db)
    assert len(ids) == 2
    count = tmp_db.execute("SELECT COUNT(*) FROM corpus_documents").fetchone()[0]
    assert count == 2
