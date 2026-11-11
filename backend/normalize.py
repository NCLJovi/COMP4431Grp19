"""Text clean-up before detection, against tricks that hide words from keyword filters.

1. Invisible format characters are removed. Scammers put them inside words, e.g. "账<U+2061>号".
2. Look-alike letters and digits become plain ones, e.g. full-width "ｈｓｂｃ" or the maths letter "𝑅".
3. Simplified Chinese becomes Traditional, so one set of rules covers both.

Detection runs on the cleaned text. `origin` maps every cleaned character back to the original, so
highlighted spans still point at the right place in what the user pasted.
"""
from __future__ import annotations

import logging
import unicodedata
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _converter():
    try:
        from opencc import OpenCC
        return OpenCC("s2t")
    except Exception:
        logger.warning("opencc is not installed, so Simplified Chinese is not converted", exc_info=True)
        return None


@lru_cache(maxsize=4096)
def to_traditional(text: str) -> str:
    """Simplified to Traditional Chinese. Also applied to the rule patterns, so both sides match."""
    converter = _converter()
    return converter.convert(text) if converter else text


def normalize(text: str) -> tuple[str, list[int]]:
    """Returns (cleaned text, original index of every cleaned character)."""
    characters: list[str] = []
    origin: list[int] = []
    for index, character in enumerate(text):
        if unicodedata.category(character) == "Cf":
            continue
        plain = unicodedata.normalize("NFKC", character)
        if plain != character and plain.isascii() and plain.isalnum():
            character = plain
        for part in character:
            characters.append(part)
            origin.append(index)
    cleaned = "".join(characters)
    converted = to_traditional(cleaned)
    # The mapping needs one character out for each character in; otherwise keep the unconverted text.
    return (converted if len(converted) == len(cleaned) else cleaned), origin


def original_span(span: list[int] | tuple[int, int] | None, origin: list[int]) -> list[int] | None:
    """Converts a [start, end) span in the cleaned text to the original text."""
    if span is None or not origin:
        return list(span) if span else span
    start, end = span
    return [origin[start], origin[end - 1] + 1] if end > start else [origin[start], origin[start]]
