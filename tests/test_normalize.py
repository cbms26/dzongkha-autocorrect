"""normalize() equivalence pairs below are grounded directly in Python's
unicodedata module (which mirrors the real Unicode Character Database), not
guessed. See dzongkha_autocorrect.normalize module docstring.
"""

from dzongkha_autocorrect.normalize import normalize

# (deprecated precomposed form, equivalent decomposed form)
# All four converge under plain NFC already since 0xF73/0xF81 have
# canonical decompositions.
CANONICAL_DECOMPOSITION_PAIRS = [
    (chr(0xF73), chr(0xF71) + chr(0xF72)),  # VOWEL SIGN II vs AA+I
    (chr(0xF75), chr(0xF71) + chr(0xF74)),  # VOWEL SIGN UU vs AA+U
    (chr(0xF81), chr(0xF71) + chr(0xF80)),  # REVERSED VOWEL SIGN AI vs AA+reversed I
]

# These two (0xF77, 0xF79) only carry a *compatibility* decomposition in
# the UCD, so plain NFC does NOT converge them with the decomposed
# spelling -- this is exactly the gap the Tibetan-block compat-decompose
# pass in normalize() closes.
COMPAT_ONLY_DECOMPOSITION_PAIRS = [
    (chr(0xF77), chr(0xFB2) + chr(0xF71) + chr(0xF80)),  # VOCALIC RR LONG
    (chr(0xF79), chr(0xFB3) + chr(0xF71) + chr(0xF80)),  # VOCALIC LL LONG
]


def test_canonical_decomposition_pairs_converge():
    for precomposed, decomposed in CANONICAL_DECOMPOSITION_PAIRS:
        assert normalize(precomposed) == normalize(decomposed)


def test_compat_only_decomposition_pairs_converge():
    for precomposed, decomposed in COMPAT_ONLY_DECOMPOSITION_PAIRS:
        assert normalize(precomposed) == normalize(decomposed)


def test_plain_nfc_alone_would_not_converge_the_compat_only_pairs():
    """Documents *why* the extra compat-decompose pass exists: bare NFC
    (with no Tibetan-specific handling) leaves these mismatched."""
    import unicodedata

    for precomposed, decomposed in COMPAT_ONLY_DECOMPOSITION_PAIRS:
        bare_nfc_precomposed = unicodedata.normalize("NFC", precomposed)
        bare_nfc_decomposed = unicodedata.normalize("NFC", decomposed)
        assert bare_nfc_precomposed != bare_nfc_decomposed


def test_idempotent():
    sample = "བཀྲ་ཤིས་བདེ་ལེགས" + chr(0xF77) + chr(0xF79)
    once = normalize(sample)
    twice = normalize(once)
    assert once == twice


def test_non_tibetan_text_passes_through_unchanged():
    assert normalize("hello world 123") == "hello world 123"


def test_empty_string():
    assert normalize("") == ""
