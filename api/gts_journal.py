"""gts.journal.*: Global Trade Station (GTS)."""
from random import choice, randint

from api.routes import Query, endpoint
from utils import areas
from utils.language import current_language
from utils.pokemon import get_random_pokemon


def _random_trade_side(by_gts_id: dict[int, dict]) -> dict:
    """Return a random trade for the GTS journal."""
    pkmn = get_random_pokemon()
    country_id = choice(list(by_gts_id))
    return {
        "country_id":   country_id,
        "country_name": by_gts_id[country_id]["names"][current_language()],
        "monsno":       pkmn["pokemon_no"],
        "form_no":      pkmn.get("form_no", 0),
        "poke_level":   randint(1, 100),
        "sex":          choice(pkmn["gender_ratio"]),
    }


@endpoint("gts.journal.trade_list")
def trade_list(_query: Query) -> dict:
    """Return a placeholder list of 100 random trades."""
    by_gts_id = areas.by_gts_id()
    return {"trade_list": [{"trade1": _random_trade_side(by_gts_id), "trade2": _random_trade_side(by_gts_id)}
                           for _ in range(100)]}
