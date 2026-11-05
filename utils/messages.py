"""Messages the server itself writes for the player (form errors, etc.).

MESSAGES is keyed by site language, then message id.
A language without a translation falls back to English.
"""
from config import DEFAULT_LANGUAGE, LANG

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "bad_nickname":       "This nickname contains inappropriate content. Please choose a new nickname.",
        "bad_gscd_length":    "Please enter a valid {length}-character Game Sync ID.",
        "gscd_not_found":     "We couldn't find that Game Sync ID. Please double-check it and try again.",
        "gscd_already_yours": "This Game Sync ID is already linked to your account.",
        "gscd_already_taken": "This Game Sync ID is already linked to another account.",
        "bad_login":          "Incorrect username or password.",
        "not_activated":      "This account hasn't been activated yet. Check your email for the activation link.",
        "most_tucked_in":     "Most Tucked-In Pokémon",
        "tuck_in_count":      "{count} times",
    },
}


def message(message_id: str, **values: object) -> str:
    """Return the message in the site language, with any {placeholders} filled in from `values`."""
    template = MESSAGES.get(LANG, {}).get(message_id) or MESSAGES[DEFAULT_LANGUAGE][message_id]
    return template.format(**values)
