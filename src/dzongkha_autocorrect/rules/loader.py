"""Loads the Phase 1 vendored syllable-structure rule data.

Source of truth: tibetan-nlp/tibetan-spellchecker, pinned at commit
04cc5f6e3a14cc72cebbb12db21a3eeecde9fdb2 — see data/SOURCES.md for the
exact upstream paths, fetch date, and per-file notes.

NOT eroux/hunspell-dz. dz.aff/dz.dic were fetched and inspected while
planning this module: dz.dic is a flat Dzongkha wordlist and dz.aff is
generic Hunspell SFX/PFX affix rules that derive grammatical suffix forms
from dictionary stems — neither encodes syllable-structure (prefix /
superscript / subjoined / vowel / suffix) legality, so hunspell-dz has no
role here. That content belongs to grammatical particles (Phase 4), and
Phase 4's own constraint requires DDC-sourced Dzongkha grammar there, not
hunspell-dz's Tibetan-derived affix rules. See data/SOURCES.md for the
full explanation.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data"

# The two known-missing commas in the vendored suffixes.json (see
# data/SOURCES.md): the bare-suffix list runs straight into the vowel-ི
# block with no separating comma, in both the "A" and "AB" keys.
_SUFFIXES_JSON_COMMA_BUG = re.compile(r'"ས"(\s*\n\s*)"ི')


@dataclass(frozen=True)
class RuleSet:
    """stacks maps a legal root-stack string (root_stacks.txt entries have
    tag 'A' or 'NB'; exceptions.txt's untagged entry maps to None) to its
    affix-class tag. suffix_classes maps a tag ('A', 'AB', or 'C') to its
    set of legal vowel+suffix combination strings, from suffixes.json.
    Not every tag in `stacks` has an entry in `suffix_classes` — 'NB' and
    None are known data gaps (see data/SOURCES.md and syllable.py).
    """

    stacks: dict[str, str | None]
    suffix_classes: dict[str, frozenset[str]]


def _read_data_text(filename: str) -> str:
    return (_DATA_DIR / filename).read_text(encoding="utf-8")


def _parse_root_stacks(text: str) -> dict[str, str]:
    """Parse data/root_stacks.txt (root_stacks.txt line 1-211, vendored
    verbatim from syllables/root.txt): one `<stack>/<tag>` entry per line.
    """
    stacks: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        stack, _, tag = line.partition("/")
        stacks[stack] = tag
    return stacks


def _parse_exceptions(text: str) -> dict[str, str | None]:
    """Parse data/exceptions.txt (vendored verbatim from
    syllables/exceptions.txt, 2 lines): 'བགླ/C' and untagged 'མདྲོན' —
    matches doc/standard-syllable-structure.md line 170's callout that
    these two stacks are valid exceptions not in the main list.
    """
    exceptions: dict[str, str | None] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "/" in line:
            stack, _, tag = line.partition("/")
            exceptions[stack] = tag
        else:
            exceptions[line] = None
    return exceptions


def _repair_suffixes_json(text: str) -> str:
    """data/suffixes.json is vendored byte-identical to upstream,
    including a known defect (see data/SOURCES.md): missing commas make it
    invalid JSON as published. Fixing the vendored copy directly would
    break the "byte-identical, diffable against upstream" guarantee, so
    the repair is applied here, at parse time, instead.
    """
    repaired, count = _SUFFIXES_JSON_COMMA_BUG.subn(r'"ས",\1"ི', text)
    if count != 2:
        raise ValueError(
            "expected exactly 2 occurrences of the known suffixes.json "
            f"comma bug (the 'A' and 'AB' keys), found {count} — the "
            "vendored file may have changed; re-verify against data/SOURCES.md"
        )
    return repaired


def _parse_suffix_classes(raw_json_text: str) -> dict[str, frozenset[str]]:
    repaired = _repair_suffixes_json(raw_json_text)
    data = json.loads(repaired)
    return {tag: frozenset(values) for tag, values in data.items()}


@lru_cache(maxsize=1)
def load_ruleset() -> RuleSet:
    """Parse and cache the vendored rule data. The data files never change
    at runtime, so this is safe to memoize for the life of the process.
    """
    stacks: dict[str, str | None] = dict(_parse_root_stacks(_read_data_text("root_stacks.txt")))
    stacks.update(_parse_exceptions(_read_data_text("exceptions.txt")))

    suffix_classes = _parse_suffix_classes(_read_data_text("suffixes.json"))

    return RuleSet(stacks=stacks, suffix_classes=suffix_classes)
