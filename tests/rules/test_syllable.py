"""Tests for validate_syllable/check_text.

Every case here is derived directly from the vendored source data (root
stacks + suffix classes) or from doc/standard-syllable-structure.md /
doc/finding-main-stack.md's own examples — no invented test syllables, per
the Phase 1 constraint that rules must be ported, not invented.
"""

from __future__ import annotations

from dzongkha_autocorrect.rules.syllable import check_text, split_syllables, validate_syllable

TSEG = "་"


# (a) known-legal stack + known-legal suffix combo -> valid.
# "ཀི" is doc/standard-syllable-structure.md's own explicit-vowel example
# (line 64); "ཀ" is tagged A (data/root_stacks.txt line 1) and bare "ི" is
# in class A (data/suffixes.json).
def test_valid_main_letter_plus_vowel():
    result = validate_syllable("ཀི")
    assert result["valid"] is True


# "བཀྲ" (data/root_stacks.txt: "བཀྲ/A") + suffix "ག" (in suffixes.json
# class A) -> a realistic word-shaped legal syllable.
def test_valid_stack_plus_suffix():
    result = validate_syllable("བཀྲག")
    assert result["valid"] is True
    assert "བཀྲ" in result["reason"]


# (b) legal stack + a suffix combo not in its class list -> invalid, with
# the "confirmed" wording (no legal decomposition), not the NB/gap wording.
def test_invalid_no_legal_decomposition():
    result = validate_syllable("ཀཏ")
    assert result["valid"] is False
    assert "no legal decomposition" in result["reason"]
    assert "needs human review" not in result["reason"]


# (c) an NB-tagged stack with no suffix ("དཀ/NB", data/root_stacks.txt
# line 5) -> valid=False, but with the data-gap reason text, distinctly
# worded from case (b)'s confirmed-invalid wording.
def test_nb_tagged_stack_is_a_data_gap_not_a_confirmed_error():
    result = validate_syllable("དཀ")
    assert result["valid"] is False
    assert "needs human review" in result["reason"]
    assert "NB" in result["reason"]


# (d) bare འ suffix on a prefix-only stack -> valid. "བཀ" (data/root_stacks
# .txt line 9, "བཀ/NB") is a legal prefix (བ) + bare main letter (ཀ), no
# superscript/subscript, satisfying doc/standard-syllable-structure.md
# lines 189-198's bare-འ-suffix condition regardless of its NB affix tag
# (that rule is checked separately from the suffix-class lookup).
def test_bare_a_suffix_on_prefix_plus_main_is_valid():
    result = validate_syllable("བཀའ")
    assert result["valid"] is True
    assert "bare" in result["reason"]


# (e) bare འ suffix on a stack with a superscript -> invalid. "རྐ"
# (data/root_stacks.txt line 13, "རྐ/A") is superscript ར + main ཀ, so it
# fails the "no superscript" condition for the bare-འ suffix.
def test_bare_a_suffix_on_stack_with_superscript_is_invalid():
    result = validate_syllable("རྐའ")
    assert result["valid"] is False


# doc/standard-syllable-structure.md lines 199-200: the doc explicitly
# calls བརྡའ a *misspelling* that does NOT follow the bare-འ-suffix rule
# (it has a superscript ར), so it must NOT validate as legal.
def test_doc_counter_example_bare_a_with_superscript_is_invalid():
    result = validate_syllable("བརྡའ")
    assert result["valid"] is False


# (f) one of doc/finding-main-stack.md's 9 documented ambiguous cases
# (lines 26-37) -> still valid, because *a* legal split exists (མ|ངས,
# per the doc's own "reasonably probable" disambiguation, line 47), even
# though this module doesn't implement the full disambiguation algorithm.
def test_ambiguous_case_from_finding_main_stack_is_still_valid():
    result = validate_syllable("མངས")
    assert result["valid"] is True


def test_split_syllables_on_tseg():
    text = f"ཀིག{TSEG}བཀྲག"
    assert split_syllables(text) == ["ཀིག", "བཀྲག"]


def test_check_text_normalizes_and_reports_offsets():
    text = f"ཀིག{TSEG}ཀཏ"
    flagged = check_text(text)
    assert len(flagged) == 1
    span = flagged[0]
    assert span["span"] == "ཀཏ"
    assert text[span["start"] : span["end"]] == "ཀཏ"
    assert set(span.keys()) == {"span", "start", "end", "reason"}


def test_check_text_no_flags_for_all_valid_text():
    text = f"ཀིག{TSEG}བཀྲག"
    assert check_text(text) == []
