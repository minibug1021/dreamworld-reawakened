"""Nickname filter.

It has regex patterns to block (badword/block.txt) and substrings that exempt a name
from them (badword/allow.txt).
"""
import re

from config import ROOT_DIR

BLOCK_PATH = ROOT_DIR / "badword" / "block.txt"
ALLOW_PATH = ROOT_DIR / "badword" / "allow.txt"


def _load_block_patterns() -> list[re.Pattern]:
    return [
        re.compile(line, re.IGNORECASE)
        for line in BLOCK_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _load_allow_words() -> list[str]:
    return [
        line.strip().lower()
        for line in ALLOW_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


_BLOCK_PATTERNS = _load_block_patterns()
_ALLOW_WORDS = _load_allow_words()


def contains_bad_word(name: str) -> bool:
    """Check `name` against badword/block.txt, exempting anything covered by badword/allow.txt."""
    if not name:
        return False

    lowered = name.lower()
    if any(allowed in lowered for allowed in _ALLOW_WORDS):
        return False

    return any(pattern.search(name) for pattern in _BLOCK_PATTERNS)
