"""pdw.home.*: the player's house and island (pdw_home.swf, pdw_room.swf)."""
import time
from random import choice, randint

from api.routes import Query, endpoint
from utils import pokemon, save_data, text
from utils.constants import NATURE_COUNT, PlayerStatus
from utils.decor import HOUSE_ISLAND_IDS, HOUSE_SHELF_IDS, arranged_decor
from utils.models import Member


@endpoint("pdw.home.footprint_list")
def footprint_list(_query: Query) -> dict:
    """Return placeholder random footprints from made-up visitors."""
    footprints = []
    for _ in range(10):
        pkmn = pokemon.get_random_pokemon()
        footprints.append({
            "is_pdw":           randint(0, 1),
            "is_gts":           randint(0, 1),
            "is_ds":            randint(0, 1),
            "friend_type":      randint(0, 2),
            "updated_at":       "2026/05/06 22:00",
            "pokemon_nickname": "pokemon_nickname",
            "pokemon_name":     text.lookup_str("pokemon", pkmn["pokemon_no"]),
            "pgl_name":         "pgl_name",
            "pokemon_no":       pkmn["pokemon_no"],
            "form_no":          pkmn.get("form_no", 0),
            # the rest is used for the popup menu
            "oyaname":          "oyaname",
            "level":            pkmn["level"],
            "type1":            text.lookup_str("type", pkmn["type1"]),
            "type2":            text.lookup_str("type", pkmn["type2"]),
            "sex_id":           choice(pkmn["gender_ratio"]),
            "personality":      text.lookup_str("nature", randint(0, NATURE_COUNT - 1)),
            "exchange_flag":    randint(0, 1),
            "water_flag":       randint(0, 1),
        })
    return {"list": footprints}


def _randomize_house() -> Member:
    """Give the player a random house and shelf, and return the updated member."""
    return save_data.update_member({"island_id": choice(HOUSE_ISLAND_IDS), "shelf_id": choice(HOUSE_SHELF_IDS)})


@endpoint("pdw.home.my_island")
def my_island(_query: Query) -> dict:
    """Return the player's island with their house, its furniture, and the tucked-in Pokémon."""
    member = _randomize_house()
    pkmn = pokemon.get_sleeper()
    return {
        "pokemon": {
            **pkmn,
            "pokemon_name": text.lookup_str("pokemon", pkmn["pokemon_no"]),
            "type1":        text.lookup_str("type", pkmn["type1"]),
            "type2":        text.lookup_str("type", pkmn["type2"]),
            "personality":  text.lookup_str("nature", pkmn["personality"]),
            "ball_name":    text.lookup_str("ball", pkmn["ball_name"]),
            "shiny":        pokemon.shows_shiny(pkmn.get("is_shiny", False)),
        },
        "island_id":              member["island_id"],
        "point":                  0,
        "trial_flag":             0,
        "arranged_interior_list": arranged_decor(),
        "requested_flag":         False,
        "shelf_id":               member["shelf_id"],
        "item_deleted_flag":      member.get("item_deleted_flag", 0),
    }


@endpoint("pdw.home.my_island_area")
def my_island_area(_query: Query) -> dict:
    """Return a placeholder of the player's island with made-up neighbors."""
    friends = [
        {
            "pgl_name":           "OtherPlayerName",
            "member_id":          randint(1, 50000),
            "member_savedata_id": randint(1, 50000),
            "island_id":          choice(HOUSE_ISLAND_IDS),
            "country_id":         randint(1, 190),
            "is_ds":              randint(0, 1),
            "is_gts":             randint(0, 1),
            "is_pdw":             randint(0, 1),
        }
        for _ in range(5)
    ]
    return {"island_id": save_data.read_member()["island_id"], "friend_list": friends}


@endpoint("pdw.home.pdw_end")
def pdw_end(_query: Query) -> dict:
    """End the Dream World session so the Pokémon can be woken."""
    save_data.set_play_status(PlayerStatus.WAKE_READY)
    return {}


@endpoint("pdw.home.pdw_start", methods=("POST",))
def pdw_start(_query: Query) -> dict:
    """Start a Dream World session."""
    timestamp = int(time.time())
    member = save_data.read_member()

    save_data.record_session_start(timestamp)
    update: Member = {"pokemon_name": text.lookup_str("pokemon", member["pokemon_no"]), "point": 0}
    if member.get("first_flag") == 0:
        update["first_flag"] = 1
    save_data.update_member(update)

    return {"started_at": timestamp}


@endpoint("pdw.home.pdw_timecheck", methods=("POST",))
def pdw_timecheck(_query: Query) -> dict:
    """Save how long is left before the next session can start."""
    save_data.update_member({"nextstart_remaintime": save_data.get_nextstart_remaintime()})
    return {}


@endpoint("pdw.home.item_deleted_check", methods=("POST",))
def item_deleted_check(_query: Query) -> dict:
    """Shown once after Berries were converted to Dream Points (see pgl_top._check_item_deletion)."""
    exchange_point = save_data.read_member().get("item_deleted_point", 0)
    save_data.update_member({"item_deleted_flag": 0, "item_deleted_point": 0})
    return {"exchange_point": exchange_point}
