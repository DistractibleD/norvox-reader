"""Lightweight offline English-vs-Norwegian guesser (no external dependency).

Good enough to pick a voice automatically; not a general-purpose language
detector. Falls back to English when the text is too short or ambiguous.
"""

import re

_NORWEGIAN_CHARS = set("æøåÆØÅ")

_NORWEGIAN_WORDS = {
    "og", "det", "er", "jeg", "du", "ikke", "en", "et", "som", "på", "med",
    "for", "til", "av", "de", "vi", "har", "kan", "skal", "vil", "var",
    "den", "dette", "denne", "hva", "hvor", "hvordan", "hvorfor", "men",
    "eller", "om", "så", "bare", "også", "her", "der", "nå", "da", "man",
    "seg", "sin", "sitt", "sine", "være", "blir", "ble", "må", "skole",
    "boka", "boken", "kapittel", "side", "oppgave", "elev", "lærer",
}

_ENGLISH_WORDS = {
    "the", "and", "is", "you", "not", "a", "an", "that", "on", "with",
    "for", "to", "of", "they", "we", "have", "can", "shall", "will",
    "was", "this", "what", "where", "how", "why", "but", "or", "if",
    "just", "also", "here", "there", "now", "then", "one", "be",
    "book", "chapter", "page", "exercise", "student", "teacher",
}

_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)


def detect_language(text: str) -> str:
    """Returns 'no' for Norwegian, 'en' for English (default)."""
    if not text or not text.strip():
        return "en"

    if any(ch in _NORWEGIAN_CHARS for ch in text):
        return "no"

    words = [w.lower() for w in _WORD_RE.findall(text)]
    if not words:
        return "en"

    no_score = sum(1 for w in words if w in _NORWEGIAN_WORDS)
    en_score = sum(1 for w in words if w in _ENGLISH_WORDS)

    if no_score == 0 and en_score == 0:
        return "en"
    return "no" if no_score > en_score else "en"
