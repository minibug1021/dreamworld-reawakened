"""Language codes and per-language formats.

LANGCODES is also used by the game-sync server.
"""
from datetime import datetime

from config import LANG

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


def localize_last_up_time(timestamp: int) -> str:
    """Format an epoch as a date and time in the site language's format."""
    return datetime.fromtimestamp(timestamp).strftime(_LAST_UP_TIME_FORMATS[LANG])
