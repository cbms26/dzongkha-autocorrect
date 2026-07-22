import sys

import pytest

from dzongkha_autocorrect.cli import reviewer


def test_add_refuses_when_stdin_is_not_a_tty(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    db_path = tmp_path / "test.db"

    with pytest.raises(SystemExit) as exc_info:
        reviewer.main(["--db-path", str(db_path), "add"])

    assert exc_info.value.code == 1
    assert "refusing to auto-populate gold" in capsys.readouterr().err.lower()


def test_promote_refuses_when_stdin_is_not_a_tty(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    db_path = tmp_path / "test.db"

    with pytest.raises(SystemExit) as exc_info:
        reviewer.main(["--db-path", str(db_path), "promote", "1"])

    assert exc_info.value.code == 1
    assert "refusing to auto-populate gold" in capsys.readouterr().err.lower()


def test_list_and_stats_run_without_a_tty(tmp_path, monkeypatch, capsys):
    """list/stats are read-only and safe to run non-interactively."""
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    db_path = tmp_path / "test.db"

    reviewer.main(["--db-path", str(db_path), "stats"])
    reviewer.main(["--db-path", str(db_path), "list"])

    out = capsys.readouterr().out
    assert "total gold rows: 0" in out
