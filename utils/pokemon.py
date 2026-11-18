"""Pokémon species data (json_data/pokemon.json) and the player's tucked-in Pokémon."""
from collections import defaultdict
from random import choice
from typing import Any, cast

from flask import session

from game_sync_server.entralinked.utility.db_manager import db
from utils import save_data
from utils.account_manager import accounts
from utils.data import load_json_data
from utils.models import SleepingPokemon

# keyed "<natdex>-<form name>", forms in form_no order
POKEMON_INFO: dict[str, dict[str, Any]] = load_json_data("pokemon")


def natdex(key: str) -> int:
    """Return the National Dex number of a POKEMON_INFO key."""
    return int(key.split("-")[0])


FORM_KEYS: dict[int, list[str]] = defaultdict(list)  # natdex -> POKEMON_INFO keys, by form_no
for _key in POKEMON_INFO:
    FORM_KEYS[natdex(_key)].append(_key)


def info(pokemon_no: int, form_no: int = 0) -> dict[str, Any]:
    """Return the POKEMON_INFO entry for a form."""
    return POKEMON_INFO[FORM_KEYS[pokemon_no][form_no]]


def get_sleeper(gscd: str | None = None) -> SleepingPokemon:
    """Return the player's tucked-in Pokémon ({} if none)."""
    gscd = save_data.resolve_gscd(gscd)
    if not gscd:
        return {}
    return cast(SleepingPokemon, db.read(gscd, "sleeping_pokemon") or {})


def shows_shiny(is_shiny: bool) -> bool:
    """Return whether to draw a Pokémon as shiny for the logged-in account.

    It has to be shiny and the account must have the shiny toggle enabled.
    """
    return is_shiny and accounts.get_shows_shiny(session.get("username"))


def get_random_pokemon() -> dict[str, Any]:
    """Return a random Pokémon's POKEMON_INFO entry, plus its National Dex number as 'pokemon_no'."""
    key = choice(list(POKEMON_INFO))
    return {**POKEMON_INFO[key], "pokemon_no": natdex(key)}
