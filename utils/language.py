"""Language codes and per-language formats.

LANGCODES is also used by the game-sync server.
"""
from datetime import datetime

from flask import has_request_context, request

from config import DEFAULT_LANGUAGE, DEFAULT_SITE_LANGUAGE, SUPPORTED_LANGUAGES

# DS cartridge langcode -> site language
LANGCODES = {
    1: "ja",
    2: "en",
    3: "fr",
    4: "it",
    5: "de",
    7: "es",
    8: "ko",
}

_LAST_UP_TIME_FORMATS = {
    "ja": "%y/%m/%d %H:%M",
    "en": "%m/%d/%y %H:%M",
    "fr": "%d/%m/%y %H:%M",
    "it": "%d/%m/%y %H:%M",
    "de": "%d.%m.%y %H:%M",
    "es": "%d-%m-%y %H:%M",
    "ko": "%y.%m.%d %H:%M",
}


LANGUAGE_COOKIE = "dw_lang"  # set by the language links (api/server.py)


def current_language() -> str:
    """Return the visitor's site language."""
    if has_request_context():
        chosen = request.cookies.get(LANGUAGE_COOKIE)
        if chosen in SUPPORTED_LANGUAGES:
            return chosen
    return DEFAULT_SITE_LANGUAGE


def game_language(langcode: int | None) -> str:
    """Return the language of a cartridge."""
    return LANGCODES.get(langcode, DEFAULT_LANGUAGE)


def localize_last_up_time(timestamp: int) -> str:
    """Format an epoch as a date and time in the visitor's language's format."""
    return datetime.fromtimestamp(timestamp).strftime(_LAST_UP_TIME_FORMATS[current_language()])
