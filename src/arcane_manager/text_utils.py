from __future__ import annotations

from .platform import Any, unicodedata
from .constants import TRANSCRIPT_NORMALIZATION_REPLACEMENTS
from .resources import MAX_ALIAS_CHARS, MAX_SHORT_FIELD_CHARS

def normalize(text: str) -> str:
    """Normalize spoken commands and aliases for reliable lookup."""
    folded = unicodedata.normalize("NFKD", text.lower())
    ascii_text = folded.encode("ascii", "ignore").decode("ascii")
    cleaned = []
    for char in ascii_text:
        cleaned.append(char if char.isalnum() else " ")
    return " ".join("".join(cleaned).split())


def normalize_transcript_for_matching(text: str) -> str:
    words = normalize(text).split()
    expanded_words = []
    for word in words:
        replacement = TRANSCRIPT_NORMALIZATION_REPLACEMENTS.get(word, word)
        expanded_words.extend(replacement.split())

    normalized_words = []
    for index, word in enumerate(expanded_words):
        previous_word = expanded_words[index - 1] if index > 0 else ""
        next_word = expanded_words[index + 1] if index + 1 < len(expanded_words) else ""
        if word in {"i", "e"} and previous_word == "fuoco" and next_word == "ritardata":
            continue
        normalized_words.append(word)
    return " ".join(normalized_words)


def clean_text(value: Any, max_chars: int = MAX_SHORT_FIELD_CHARS) -> str:
    """Convert untrusted JSON values to safe, bounded display text."""
    if value is None:
        return ""
    text = str(value)
    text = "".join(char for char in text if char in "\n\t" or not unicodedata.category(char).startswith("C"))
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if len(text) > max_chars:
        return text[: max_chars - 1].rstrip() + "…"
    return text


def clean_text_list(values: Any, max_items: int, max_chars: int) -> tuple[str, ...]:
    if not isinstance(values, list):
        return ()
    cleaned = []
    for value in values[:max_items]:
        text = clean_text(value, max_chars)
        if text:
            cleaned.append(text)
    return tuple(dict.fromkeys(cleaned))
