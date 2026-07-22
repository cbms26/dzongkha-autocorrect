"""Normalization for Dzongkha (Tibetan-script) text.

Must run before any storage, lookup, or comparison, everywhere in this
codebase, so that visually identical syllables become byte-identical.

Two layers, in order:

1. A Tibetan-block "compatibility decomposition" pass. A handful of
   deprecated Tibetan vowel-sign codepoints (currently U+0F77, U+0F79 —
   Sanskrit-transliteration "vocalic RR/LL long" signs) carry only a
   *compatibility* decomposition in the Unicode Character Database, not a
   canonical one (verified directly against Python's ``unicodedata``, which
   mirrors the real UCD — see tests/test_normalize.py). Plain NFC only
   follows canonical decompositions, so these would NOT converge with an
   already-decomposed spelling of the same syllable under NFC alone. NFKC
   would catch this, but NFKC also collapses other, meaningful, Tibetan
   distinctions, so instead this module applies compatibility decomposition
   narrowly, to the Tibetan block only, driven directly by ``unicodedata``
   (not a hand-guessed table).
2. Standard Unicode NFC, which handles canonical decomposition of the
   remaining deprecated precomposed vowel signs (e.g. U+0F73, U+0F81) and
   canonical reordering of combining marks by combining class.

This does NOT attempt to resolve non-canonical input-order ambiguities that
are outside the Unicode Character Database (e.g. a user typing a vowel sign
and a subjoined consonant in an unexpected order that some renderers
tolerate). Those require Tibetan-script-specific rules sourced from a real
reference implementation (e.g. botok's cleanup helpers) or DDC guidance, not
invention here — see the optional botok pass below, which is a stub pending
that source material (tracked as a Phase-2 open item; botok also needs a
Python-version compatibility decision before it can be relied on — see
CLAUDE.md / the Phase 0 plan).
"""

from __future__ import annotations

import os
import unicodedata

_TIBETAN_BLOCK_START = 0x0F00
_TIBETAN_BLOCK_END = 0x0FFF

_BOTOK_ENV_VAR = "DZA_USE_BOTOK"


def normalize(text: str) -> str:
    """Normalize Dzongkha text so equivalent input converges to one form.

    Must be called before any DB write, lookup, or comparison.
    """
    text = _decompose_tibetan_compat(text)
    text = unicodedata.normalize("NFC", text)
    if _botok_enabled():
        text = _botok_cleanup(text)
    return text


def _decompose_tibetan_compat(text: str) -> str:
    """Expand Tibetan-block codepoints whose only UCD decomposition is a
    compatibility (not canonical) mapping, so a later NFC pass can converge
    them with an equivalent already-decomposed spelling.
    """
    out: list[str] = []
    for ch in text:
        cp = ord(ch)
        if _TIBETAN_BLOCK_START <= cp <= _TIBETAN_BLOCK_END:
            decomp = unicodedata.decomposition(ch)
            if decomp.startswith("<"):
                out.append(
                    "".join(chr(int(part, 16)) for part in decomp.split()[1:])
                )
                continue
        out.append(ch)
    return "".join(out)


def _botok_enabled() -> bool:
    return os.environ.get(_BOTOK_ENV_VAR, "") == "1"


def _botok_cleanup(text: str) -> str:
    try:
        import botok  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            f"{_BOTOK_ENV_VAR}=1 is set but botok is not installed. "
            "Install the optional extra: uv sync --extra botok"
        ) from exc
    # botok's exact cleanup-helper API has not been verified against this
    # project's Python version yet (see the Phase 0 plan's flagged open
    # item on botok/Python-3.14 compatibility). Wiring a real call here
    # without having confirmed the API would risk baking in a guess at the
    # normalization layer everything else depends on, so this intentionally
    # stops short rather than fabricating the integration.
    raise NotImplementedError(
        "botok cleanup pass is not yet wired up (Phase 2 prerequisite)."
    )
