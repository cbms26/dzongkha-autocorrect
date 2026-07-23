# Vendored source data — provenance

All files in this directory (except this one) are byte-identical copies of
files fetched directly from the upstream repository below. They are vendored
rather than fetched at runtime because the Phase 1 constraint is "no network
calls at runtime." Do not hand-edit them — see `loader.py` for how known
upstream defects are repaired defensively at parse time instead of by
editing the vendored copy, so the copies stay diffable against upstream.

- **Upstream repo:** https://github.com/tibetan-nlp/tibetan-spellchecker
- **Pinned commit:** `04cc5f6e3a14cc72cebbb12db21a3eeecde9fdb2`
- **Fetch date:** 2026-07-23

## Files

| Vendored file       | Upstream path                    | Notes |
|----------------------|-----------------------------------|-------|
| `root_stacks.txt`    | `syllables/root.txt`             | 211 lines. Each line is `<stack>/<tag>`, tag is `A` or `NB` (a Hunspell-style affix-class flag). `NB`'s legal-suffix set is not resolvable from data in hand — it references an `.aff` file that lives in a different, unfetched repo (`eroux/hunspell-bo`). |
| `exceptions.txt`     | `syllables/exceptions.txt`       | 2 lines: `བགླ/C` and untagged `མདྲོན`. Matches `doc/standard-syllable-structure.md` line 170's callout that TSH excludes these from its main list but treats them as valid exceptions. |
| `suffixes.json`      | `syllables/suffixes.json`        | 3 suffix classes (`A`, `AB`, `C`), each a list of legal vowel+suffix combination strings. **Vendored with a known upstream defect intact**: invalid JSON as published — missing comma between the bare-suffix list and the vowel-ི block, in both the `A` and `AB` keys (`json.loads` fails at line 3 col 9). `loader.py` repairs this at parse time; the vendored copy is left byte-identical to upstream on purpose. |

Also consulted (not vendored — prose reference only, cited by line number in
code comments, not parsed programmatically):

- `doc/standard-syllable-structure.md` — the full prose rule set. Cited
  sections: legal prefixes (lines 25-29), legal superscript+main+subscript+
  2nd-subscript stacks (lines 115-129), legal prefix+superscript+main+
  subscript combos (lines 137-169), suffix list (lines 71-85), second-suffix
  constraints (lines 174-187), bare-འ-suffix rule (lines 189-198).
- `doc/finding-main-stack.md` — a natural-language main-stack-disambiguation
  algorithm with 9 explicitly-enumerated ambiguous cases. Not needed for the
  core validity check (see `syllable.py` module docstring for why), but its
  9 ambiguous cases are used as informational test cases in
  `tests/rules/test_syllable.py`.
- `syllables/README.md` — confirms these files are hunspell-`.dic`-format
  data, and notes simplifications already baked into them (e.g. all wasur
  syllables listed explicitly rather than a general wasur rule; archaic
  forms excluded).

## Why not `eroux/hunspell-dz`?

The Phase 1 plan's deliverable #3 originally called for "a loader that
imports the hunspell-dz rule/affix data as the source of truth." `dz.aff`
and `dz.dic` were fetched and inspected directly before writing this module:
`dz.dic` is a flat Dzongkha wordlist, and `dz.aff` is generic Hunspell
SFX/PFX affix rules that derive grammatical suffix forms (ཡི, འོ, ར, ས, ...)
from dictionary stems. Neither encodes syllable-*structure*
(prefix/superscript/subjoined/vowel/suffix) legality — that content belongs
to grammatical particles, which is Phase 4's domain, not Phase 1's. Phase
4's own constraint requires DDC-sourced Dzongkha grammar there (not
hunspell-dz's Tibetan-derived affix rules), so hunspell-dz has no remaining
role even in the phase its actual content would otherwise fit. This module's
source of truth is `tibetan-nlp/tibetan-spellchecker` instead, per the
Phase 1 plan's own priority ("port ... from the tibetan-spellchecker and
hunspell-dz repos — do NOT invent rules": tibetan-spellchecker is where the
real, citable structural rule data lives).
