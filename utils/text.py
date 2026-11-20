"""Localized strings from raw_text/<lang>/<type>.txt.

Line N of each file holds the string with id N, counting from 0. A blank line means that id
has no string.
"""
from functools import cache

from config import ROOT_DIR
from utils.language import current_language

DESCRIPTION_LINES = 3  # *_descriptions entries have up to 3 lines, separated by a literal \n


@cache
def _strings(lang: str, str_type: str) -> list[str]:
    return (ROOT_DIR / "raw_text" / lang / f"{str_type}.txt").read_text(encoding="utf-8").splitlines()


def lookup_str(str_type: str, string_id: int | None, lang: str | None = None) -> str | None:
    """Return the string with this id, or None if the id has none."""
    strings = _strings(lang or current_language(), str_type)
    if string_id is None or not 0 <= string_id < len(strings):
        return None
    return strings[string_id] or None


def lookup_description(str_type: str, string_id: int | None, lang: str | None = None) -> list[str | None]:
    """Return a *_descriptions entry split into lines.

    The list is padded with None to at least DESCRIPTION_LINES (all None if the id
    doesn't exist).
    """
    entry = lookup_str(str_type, string_id, lang)
    lines: list[str | None] = list(entry.split("\\n")) if entry is not None else []
    return lines + [None] * (DESCRIPTION_LINES - len(lines))
