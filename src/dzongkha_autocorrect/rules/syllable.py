"""Rule-based Dzongkha syllable-structure validator (Phase 1 — script layer).

This validates that a syllable's prefix/superscript/main/subscript/vowel/
suffix combination is a *structurally legal Tibetan-script stack*. Per
CLAUDE.md's "Dzongkha is not Tibetan" principle, that is legitimately
reusable Tibetan-tooling territory: a well-formed Tibetan-script syllable
is well-formed in Dzongkha too. This module says nothing about whether a
structurally-legal syllable is an actual Dzongkha *word* — that is a
Phase 2 dictionary question, sourced from DDC, not from this data.

Validation algorithm: rather than porting doc/finding-main-stack.md's
natural-language main-stack-disambiguation algorithm (see
rules/data/SOURCES.md) as executable logic, validate_syllable tries every
split point of the syllable and accepts it if any split has a stem in the
vendored legal root-stack set (root_stacks.txt + exceptions.txt already
bake in prefix+superscript+main+subscript combinations, see
doc/standard-syllable-structure.md lines 137-169) and a suffix in that
stem's legal suffix-class set (suffixes.json), or matches the separate
bare-འ-suffix rule below. This is equivalent in outcome to the prose
algorithm — if a legal decomposition exists at all, the syllable is
structurally legal — without re-encoding finding-main-stack.md's 9
documented ambiguous cases (see tests/rules/test_syllable.py, which uses
those 9 cases as informational, not-a-failure, test cases).
"""

from __future__ import annotations

import re
from typing import TypedDict

from dzongkha_autocorrect.normalize import normalize
from dzongkha_autocorrect.rules.loader import load_ruleset

TSEG = "་"  # ་

# doc/standard-syllable-structure.md lines 189-198: the bare འ suffix is
# legal only in syllables with one prefix, no superscript, no subscript,
# no vowel. suffixes.json's class lists never include bare འ (only the
# grammatical forms འི/འོ/འང/འམ), so this is checked separately.
_BARE_A_SUFFIX = "འ"  # འ

# doc/standard-syllable-structure.md lines 25-29: the five legal prefixes.
_PREFIXES = frozenset("གདབམའ")  # ག ད བ མ འ

# Tibetan-block subjoined ("stacked-below") consonant codepoints. A
# 2-codepoint stem is "prefix + bare main letter, no superscript/subscript"
# (the bare-འ-suffix condition) only if its second codepoint is NOT one of
# these — a stacked (superscript+main or main+subscript) reading always
# puts the *lower* member of the stack in this range. The source doc states
# the condition in prose only; this codepoint check is this module's own
# translation of it, not a rule ported verbatim from source.
_SUBJOINED_START = 0x0F90
_SUBJOINED_END = 0x0FBC

# Characters that can appear inside a syllable's consonant/vowel stack:
# base consonants (U+0F40-U+0F6C), subjoined consonants (U+0F90-U+0FBC),
# and vowel signs (U+0F71-U+0F84). Used only to find syllable spans in
# running text (i.e. as the inverse of tseg/shad/whitespace/punctuation);
# legality of what's found is decided by validate_syllable, not by this
# character class.
_SYLLABLE_CHARS = re.compile("[ཀ-ཬྐ-ྼཱ-྄]+")


class SyllableResult(TypedDict):
    valid: bool
    reason: str


class FlaggedSpan(TypedDict):
    span: str
    start: int
    end: int
    reason: str


def split_syllables(text: str) -> list[str]:
    """Split already-normalized text on tseg and other non-syllable
    characters, returning the syllable-content runs. Callers with raw text
    should normalize first (see check_text).
    """
    return _SYLLABLE_CHARS.findall(text)


def _is_bare_prefix_plus_main(stem: str) -> bool:
    """True if `stem` is exactly one legal prefix letter followed by one
    base (non-subjoined) main letter — the bare-འ-suffix condition from
    doc/standard-syllable-structure.md lines 189-198 ("one prefix, no
    superscript, no subscript, no vowel"), translated into codepoint
    structure. See the _SUBJOINED_START/_SUBJOINED_END comment above.
    """
    if len(stem) != 2:
        return False
    if stem[0] not in _PREFIXES:
        return False
    return not (_SUBJOINED_START <= ord(stem[1]) <= _SUBJOINED_END)


def validate_syllable(syl: str) -> SyllableResult:
    """Validate one already-normalized syllable's structural legality.

    Expects `syl` to already be normalized (the normal call path is via
    check_text, which normalizes first). This function does not
    re-normalize per-syllable, so a caller invoking it directly is
    responsible for calling dzongkha_autocorrect.normalize.normalize first.
    """
    ruleset = load_ruleset()
    gap_reason: str | None = None

    for i in range(len(syl), -1, -1):
        stem, suffix = syl[:i], syl[i:]
        if stem not in ruleset.stacks:
            continue
        tag = ruleset.stacks[stem]

        if suffix == _BARE_A_SUFFIX:
            if tag is not None and _is_bare_prefix_plus_main(stem):
                return {
                    "valid": True,
                    "reason": (
                        f"stem '{stem}' + bare {_BARE_A_SUFFIX} suffix is legal "
                        "per the bare-suffix rule "
                        "(doc/standard-syllable-structure.md lines 189-198): a "
                        "single prefix + main letter, no superscript/subscript/vowel"
                    ),
                }
            continue

        if tag is None:
            if suffix == "":
                return {
                    "valid": True,
                    "reason": (
                        f"stem '{stem}' matches a vendored exception with no "
                        "suffix (data/exceptions.txt line 2); no suffix-class "
                        "data is available for this entry"
                    ),
                }
            if gap_reason is None:
                gap_reason = (
                    f"root stack '{stem}' is a vendored exception "
                    "(data/exceptions.txt line 2) with no affix-class tag, so "
                    "its legal suffix set is unknown — needs human review, not "
                    "a confirmed error"
                )
            continue

        suffix_set = ruleset.suffix_classes.get(tag)
        if suffix_set is not None:
            if suffix in suffix_set:
                return {
                    "valid": True,
                    "reason": (
                        f"stem '{stem}' (data/root_stacks.txt, class {tag}) + "
                        f"suffix '{suffix}' (data/suffixes.json, class {tag}) is "
                        "a legal combination"
                    ),
                }
            continue

        if gap_reason is None:
            gap_reason = (
                f"root stack '{stem}' is structurally legal "
                f"(data/root_stacks.txt, tag {tag}) but tag '{tag}' has no "
                "suffix-class definition in the vendored data/suffixes.json "
                "(only A/AB/C are defined) — needs human review, not a "
                "confirmed error"
            )

    if gap_reason is not None:
        return {"valid": False, "reason": gap_reason}

    return {
        "valid": False,
        "reason": (
            f"no legal decomposition found for '{syl}': no split point has a "
            "stem in the vendored legal root-stack list (data/root_stacks.txt "
            "+ data/exceptions.txt) with a matching legal suffix "
            "(data/suffixes.json) or the bare-suffix exception "
            "(doc/standard-syllable-structure.md lines 189-198)"
        ),
    }


def check_text(text: str) -> list[FlaggedSpan]:
    """Normalize `text`, split it into syllables, and return every
    structurally-invalid span with its offsets in the normalized text.
    """
    normalized = normalize(text)
    flagged: list[FlaggedSpan] = []
    for match in _SYLLABLE_CHARS.finditer(normalized):
        result = validate_syllable(match.group())
        if not result["valid"]:
            flagged.append(
                {
                    "span": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "reason": result["reason"],
                }
            )
    return flagged
