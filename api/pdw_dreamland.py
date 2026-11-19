"""pdw.dreamland.*: Dream Island visits (pdw_island.swf) and their minigame rewards."""
import hashlib
import logging
from collections.abc import Sequence
from random import choices, randint, sample
from typing import TypeVar

from flask import session

from api.routes import Query, endpoint, query_int
from utils import managers, pokemon, save_data, text
from utils.constants import NATURE_COUNT, is_b2w2
from utils.data import load_json_data
from utils.models import Member

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Not post-processing any of the raw data for now.
_DREAMLAND = load_json_data("dream_islands")
# island area id (3-9) -> {"req_points": {"bw", "b2w2"}, "req_badges": {"bw", "b2w2"}}
# (type preferences: _FAVORED_AREA_SHARE)
_UNLOCKS: dict[str, dict[str, dict[str, int]]] = _DREAMLAND["unlocks"]
_SLOTS = {int(object_id): slot for object_id, slot in _DREAMLAND["objects"].items()}
_CONTENTS = {c["object_pokemon_id"]: c for slot in _SLOTS.values() for c in slot["contents"]}

OBJECTS_PER_VISIT = 17
B2W2_AREA_OFFSET = 100  # B2W2 use areas 103-109
MINIGAME_POINTS = 20
SPECIAL_MOVE_COUNT = 4  # waza_count: every live capture says 4

# Minigame rank (1 best - 5 worst) -> % chance of the Pokémon's special move A, B, or C.
# Ranks 2, 3, and 4's odds are estimated. Rank 0 is a failure.
MOVE_CHANCES = {
    0: (0, 0, 0),
    1: (0, 50, 50),
    2: (20, 40, 40),
    3: (40, 32, 28),
    4: (60, 25, 15),
    5: (70, 20, 10),
}
_VISIT_TOKENS = "dreamland_otokens"  # session key: {object_pokemon_id: otoken} for this visit

# Tucked-in Pokémon type id -> {area id: share of visits}. A type sends this share of visits to
# its favored area(s) and splits the rest evenly across every other area. A dual type averages
# its two types' tables, and areas the player can't enter yet are skipped.
_FAVORED_AREA_SHARE: dict[int, dict[str, float]] = {
    0:  {"9": 0.50},             # Normal: Dream Park (estimate)
    1:  {"6": 0.50},             # Fighting: Rugged Mountain
    2:  {"5": 0.70},             # Flying: Windswept Sky
    3:  {"3": 0.50},             # Poison: Pleasant Forest
    4:  {"6": 0.35, "8": 0.35},  # Ground: Rugged Mountain, Icy Cave
    5:  {"6": 0.35, "8": 0.35},  # Rock: Rugged Mountain, Icy Cave
    6:  {"3": 0.50},             # Bug: Pleasant Forest
    7:  {"7": 0.70},             # Ghost: Spooky Manor
    8:  {"6": 0.35, "8": 0.40},  # Steel: Rugged Mountain, Icy Cave
    9:  {"6": 0.50},             # Fire: Rugged Mountain
    10: {"4": 0.70},             # Water: Sparkling Sea
    11: {"3": 0.70},             # Grass: Pleasant Forest
    12: {"3": 0.50},             # Electric: Pleasant Forest
    13: {"7": 0.50},             # Psychic: Spooky Manor
    14: {"8": 0.70},             # Ice: Icy Cave
    15: {},                      # Dragon: no preference
    16: {"7": 0.50},             # Dark: Spooky Manor
}


def _weighted_choice(options: Sequence[T], weights: Sequence[float]) -> T:
    return choices(options, weights=weights, k=1)[0]


def _pokemon_fields(content: dict) -> dict:
    """Pokémon-related fields which are sent by both pdw.dreamland.top and game_clear."""
    info = pokemon.info(content["pokemon_no"], content["form_no"])
    return {
        "pokemon_no": content["pokemon_no"],
        "form_no":    content["form_no"],
        "pokename":   text.lookup_str("pokemon", content["pokemon_no"]),
        "sex_id":     content["sex_id"],
        "type1":      text.lookup_str("type", info["type1"]),
        "type2":      text.lookup_str("type", info["type2"]),
        "speabi1":    text.lookup_str("ability", info["speabi1"]),
        "speabi2":    text.lookup_str("ability", info["speabi2"]),
        "speabi3":    text.lookup_str("ability", info["speabi3"]),
    }


def _area_weights(type_ids: Sequence[int | None], area_ids: Sequence[str]) -> dict[str, float]:
    """Chance of each area (summing to 1) for a tucked-in Pokémon of these types. See _FAVORED_AREA_SHARE."""
    types = list(dict.fromkeys(t for t in type_ids if t is not None))  # a mono-type has type1 == type2
    weights = dict.fromkeys(area_ids, 0.0)
    for type_id in types:
        favored = {a: share for a, share in _FAVORED_AREA_SHARE[type_id].items() if a in weights}
        rest = (1 - sum(favored.values())) / (len(area_ids) - len(favored))
        for area_id in area_ids:
            weights[area_id] += favored.get(area_id, rest) / len(types)
    return weights


def _pick_area(player: Member, game_key: str) -> str:
    """Return a random area ID (3-9) from the ones accessible to the player.

    The pick is weighted by the tucked-in Pokémon's types.
    """
    points, badges = player["experiment_point"], player["player_badge_num"] or 0
    island_areas = list(_UNLOCKS)
    weights = _area_weights([player["type1"], player["type2"]], island_areas)
    areas = [area_id for area_id in island_areas
             if points >= _UNLOCKS[area_id]["req_points"][game_key]
             and badges >= _UNLOCKS[area_id]["req_badges"][game_key]]
    return _weighted_choice(areas, [weights[area_id] for area_id in areas])


def _object_entry(object_id: int, slot: dict, world_id: int) -> dict:
    """Build an encounter object, which is either a Pokémon with a mini-game or an item."""
    content = _weighted_choice(slot["contents"], [c["weight"] for c in slot["contents"]])
    entry = {
        "object_id":         object_id,
        "otoken":            save_data.generate_otoken(world_id),
        "public_date_from":  None,
        "public_date_to":    None,
        "object_category":   slot["object_category"],
        "minigame_id":       slot["minigame_id"],
        "kinomi_id":         0,
        "kinomi_count":      0,
        "pokeitem_id":       0,
        "object_pokemon_id": content["object_pokemon_id"],
    }
    if "pokemon_no" in content:
        entry["pokemon"] = {**_pokemon_fields(content), "action_type": content["action_type"]}
    return entry


def _minigame_rank(object_pokemon_id: str, result: str) -> int | None:
    """Return the mini-game rank that `result` encodes, or None if it matches none.

    pdw_island.swf sends result = md5(str(rank) + otoken + object_pokemon_id).
    """
    otoken = session.get(_VISIT_TOKENS, {}).get(object_pokemon_id)
    if otoken is None:
        return None
    for rank in MOVE_CHANCES:
        if hashlib.md5(f"{rank}{otoken}{object_pokemon_id}".encode()).hexdigest() == result:
            return rank
    return None


def _special_move(content: dict, rank: int | None) -> int | None:
    """Pick special move A, B, or C by MOVE_CHANCES for the rank.

    An unknown rank counts as rank 0. Return None if no move has a chance.
    """
    chances = MOVE_CHANCES[0 if rank is None else rank]
    possible = [(move, chance) for move, chance in zip(content["special_moves"], chances, strict=False)
                if move is not None and chance > 0]
    if not possible:
        return None
    moves, weights = zip(*possible, strict=True)
    return _weighted_choice(moves, weights)


@endpoint("pdw.dreamland.top")
def top(_query: Query) -> dict:
    """Build a Dream Island visit.

    The island is picked by the player's Dream Points, badges, and Pokémon types. Each island
    has a fixed set of object slots, unlocked by Dream Points (base pool plus expansions).
    A visit shows OBJECTS_PER_VISIT of the unlocked slots at random. Once the session's
    visits (dreamland_visits_left) are used up, the island is empty.
    """
    player = save_data.read_member()
    b2w2 = is_b2w2(player["rom_id"])
    points = player["experiment_point"]

    area_id = _pick_area(player, "b2w2" if b2w2 else "bw")
    if b2w2:
        area_id = str(int(area_id) + B2W2_AREA_OFFSET)

    if not save_data.use_dreamland_visit():
        session.pop(_VISIT_TOKENS, None)
        return {"dreamland_area_id": int(area_id), "object_list": []}

    unlocked = [object_id for object_id in _DREAMLAND["areas"][area_id]
                if _SLOTS[object_id]["min_points"] <= points]
    visit = sample(unlocked, min(OBJECTS_PER_VISIT, len(unlocked)))

    object_list = [_object_entry(object_id, _SLOTS[object_id], player["world_id"]) for object_id in visit]
    # game_clear needs each object's otoken to read the minigame rank out of `result`
    session[_VISIT_TOKENS] = {str(o["object_pokemon_id"]): o["otoken"] for o in object_list}

    return {
        "dreamland_area_id": int(area_id),
        "object_list":       object_list,
    }


@endpoint("pdw.dreamland.tree_top")
def tree_top(_query: Query) -> dict:
    """Return placeholder random Pokémon from made-up players."""
    pokemon_list = []
    for _ in range(randint(1, 10)):
        pkmn = pokemon.get_random_pokemon()
        pokemon_list.append({
            "pokemon_no":         pkmn["pokemon_no"],
            "form_no":            pkmn.get("form_no", 0),
            "pgl_name":           "PGLName",
            "member_savedata_id": 123,
            "nickname":           None,
            "pokename":           text.lookup_str("pokemon", pkmn["pokemon_no"]),
            "oyaname":            "PlayerName",
            "level":              randint(1, 100),
            "type1":              text.lookup_str("type", pkmn["type1"]),
            "type2":              text.lookup_str("type", pkmn["type2"]),
            "sex_id":             0,
            "pokekaku":           text.lookup_str("nature", randint(0, NATURE_COUNT - 1)),
            "pokeplace":          "Route 1",
            "ball_name":          text.lookup_str("ball", 4),
        })
    return {"pokemon_list": pokemon_list, "encount_list": []}


@endpoint("pdw.dreamland.game_clear", methods=("POST",))
def game_clear(query: Query) -> dict:
    """Process item rewards now, otherwise send the Pokémon reward data forward.

    The query holds `object_pokemon_id` (which content slot it was), `pokeitem_id`, and
    `result`. `pokeitem_id` is always 0 unless minigame 2 (Ice Cream Scoop) was played.
    Then it is the item id of the Berry that was used up. `result` is an MD5 of the game
    result (0 failure/abort, 1-5 success), the token, and object_pokemon_id.

    The special move (waza_name_disp) depends on the minigame rank read from result (see
    _special_move and MOVE_CHANCES). Return the reward, which is a Pokémon or an item.
    """
    logger.debug("game_clear %s", query)

    content = _CONTENTS.get(int(query["object_pokemon_id"]))
    if content is None:
        raise ValueError(f"Unknown object_pokemon_id: {query['object_pokemon_id']}")

    if "pokemon_no" in content:
        pokeitem_id = query_int(query, "pokeitem_id", 0)
        if pokeitem_id:
            managers.get_chest().remove_item(pokeitem_id, 1)

        save_data.award_points(MINIGAME_POINTS)

        rank = _minigame_rank(query["object_pokemon_id"], query.get("result", ""))
        move_id = _special_move(content, rank)
        reward = {
            "pokemon": {
                **_pokemon_fields(content),
                "waza_name_disp": text.lookup_str("move", move_id),
                "waza_count":     SPECIAL_MOVE_COUNT,
            },
            "item":     None,
            "interior": None,
            "present":  None,
        }

    else:
        item_id = content["item_id"]
        reward = {
            "pokemon": None,
            "item": {
                "pokeitem_id":   item_id,
                "pokeitem":      text.lookup_str("item", item_id),
                "poke_item_num": 1,
            },
            "interior": None,
            "present":  None,
        }

        managers.get_chest().add_item(item_id, 1)

    return reward
