"""Tests for the vendored rule-data loader.

These guard the vendoring story itself, not just the parsed output: the
vendored suffixes.json must still contain its known upstream comma bug (so
nobody "fixes" the byte-identical copy and silently breaks the cited-defect
story — see data/SOURCES.md), and the counts must match what data/SOURCES.md
claims.
"""

from __future__ import annotations

import json

import pytest

from dzongkha_autocorrect.rules.loader import (
    _DATA_DIR,
    _parse_exceptions,
    _parse_root_stacks,
    _read_data_text,
    _repair_suffixes_json,
    load_ruleset,
)


def test_data_files_exist():
    for filename in ("root_stacks.txt", "exceptions.txt", "suffixes.json", "SOURCES.md"):
        assert (_DATA_DIR / filename).is_file(), filename


def test_root_stacks_txt_has_211_entries():
    stacks = _parse_root_stacks(_read_data_text("root_stacks.txt"))
    assert len(stacks) == 211


def test_root_stacks_tags_are_a_or_nb():
    stacks = _parse_root_stacks(_read_data_text("root_stacks.txt"))
    assert set(stacks.values()) == {"A", "NB"}


def test_exceptions_txt_has_2_entries():
    exceptions = _parse_exceptions(_read_data_text("exceptions.txt"))
    assert len(exceptions) == 2
    assert exceptions["བགླ"] == "C"
    assert exceptions["མདྲོན"] is None


def test_vendored_suffixes_json_still_has_the_known_comma_bug():
    """Guards against someone "fixing" the vendored copy directly, which
    would break the byte-identical-with-upstream vendoring guarantee (the
    fix belongs in loader._repair_suffixes_json, applied at parse time).
    """
    raw_text = _read_data_text("suffixes.json")
    with pytest.raises(json.JSONDecodeError):
        json.loads(raw_text)


def test_repair_suffixes_json_produces_valid_complete_json():
    raw_text = _read_data_text("suffixes.json")
    repaired = _repair_suffixes_json(raw_text)
    data = json.loads(repaired)
    assert set(data.keys()) == {"A", "AB", "C"}
    # spot-check the exact boundary where the missing comma was
    assert "ས" in data["A"]
    assert "ི" in data["A"]
    assert "ས" in data["AB"]
    assert "ི" in data["AB"]


def test_repair_suffixes_json_raises_if_pattern_not_found():
    already_valid = '{"A": ["", "ི"], "AB": ["", "ི"], "C": [""]}'
    with pytest.raises(ValueError):
        _repair_suffixes_json(already_valid)


def test_load_ruleset_merges_root_stacks_and_exceptions():
    ruleset = load_ruleset()
    # 211 root_stacks.txt entries + 2 exceptions.txt entries, no overlap
    assert len(ruleset.stacks) == 213
    assert ruleset.stacks["ཀ"] == "A"
    assert ruleset.stacks["བགླ"] == "C"
    assert ruleset.stacks["མདྲོན"] is None


def test_load_ruleset_suffix_classes():
    ruleset = load_ruleset()
    assert set(ruleset.suffix_classes.keys()) == {"A", "AB", "C"}
    assert "" in ruleset.suffix_classes["A"]
    assert "འ" in ruleset.suffix_classes["AB"]  # AB includes bare འ, unlike A
    assert "འ" not in ruleset.suffix_classes["A"]


def test_load_ruleset_is_cached():
    assert load_ruleset() is load_ruleset()
