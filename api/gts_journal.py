"""gts.journal.*: Global Trade Station (GTS)."""
import json
import re
from functools import cache
from random import choice, randint

from api.routes import Query, endpoint
from config import LANG, ROOT_DIR
from utils.pokemon import get_random_pokemon

AREAS_JS = ROOT_DIR / "dreamworld_assets" / "shared.pokemon-gl.com" / "report" / "assets" / "js" / "areas.js"


@cache
def load_areas() -> dict[int, dict]:
    """GTS country id -> area entry from the site's areas.js."""
    match = re.search(r"var a = (\[.*?\]);", AREAS_JS.read_text(encoding="utf-8"), re.DOTALL)
    if match is None:
        raise ValueError(f"No area list found in {AREAS_JS}")
    quoted = re.sub(r"(?<=[{,])\s*([a-zA-Z_]\w*)\s*:", r'"\1":', match.group(1))
    return {entry["gts"]: entry for entry in json.loads(quoted) if entry["gts"] not in (0, None)}


def _random_trade_side(areas: dict[int, dict]) -> dict:
    """One random Pokémon and the country it was traded from."""
    pkmn = get_random_pokemon()
    country_id = choice(list(areas))
    return {
        "country_id":   country_id,
        "country_name": areas[country_id]["names"][LANG],
        "monsno":       pkmn["pokemon_no"],
        "form_no":      pkmn.get("form_no", 0),
        "poke_level":   randint(1, 100),
        "sex":          choice(pkmn["gender_ratio"]),
    }


@endpoint("gts.journal.trade_list")
def trade_list(_query: Query) -> dict:
    """Return a placeholder list of 100 random trades."""
    areas = load_areas()
    return {"trade_list": [{"trade1": _random_trade_side(areas), "trade2": _random_trade_side(areas)}
                           for _ in range(100)]}
