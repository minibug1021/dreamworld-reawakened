import json
from random import choice, choices, randint

from utils import text
from utils import pokemon
from utils import managers
from utils import save_data

encounter_store = {}

# ---------------------
# GET API calls
# ---------------------

def GET_top(_query):
    """Processes the Dream Island encounter logic based on player information.

    The Dream Island area selected is filtered based on the player's total Dream Points,
    number of badges in-game, and the type of the Pokémon being brought to the island.

    The Pokémon encountered are filtered based on the player's total Dream Points,
    number of badges in-game, and the game that was connected (BW vs B2W2).

    The items encountered are filtered based on the player's total Dream Points.

    Returns:
        A JSON-encoded bytes object representing the generated Dream Island
        encounters and its populated objects (Pokémon and items).
    """

    # --- get player game version ---
    player_data = save_data.read_player_data()["member"]

    rom_name      = player_data["rom_name"]
    player_points = int(player_data["experiment_point"])
    player_badges = int(player_data["player_badge_num"])
    player_types  = {player_data["type1"], player_data["type2"]}

    is_bw   = rom_name in ("Pokémon Black Version", "Pokémon White Version")
    is_b2w2 = rom_name in ("Pokémon Black Version 2", "Pokémon White Version 2")
    game_key = "bw" if is_bw else "b2w2"

    # --- select eligible Dream Island area ---
    eligible_areas = []
    area_weights   = []
    for area_id, area in pokemon.area_info.items():
        if area_id == "50": #we don't have the file for Pokémon Café Forest
            continue

        if player_points < area["req_points"][game_key]:
            continue

        if player_badges < area["req_badges"][game_key]:
            continue

        eligible_areas.append(area_id)

        # Bulbapedia says Pokemon with a "favored type" bring you to certain areas more often, so for right now its a 25% boost
        weight = 1.25 if player_types & set(area["favored_types"]) else 1.0
        area_weights.append(weight)

    dreamland_area_id = choices(eligible_areas, weights=area_weights, k=1)[0]

    area = pokemon.area_info[dreamland_area_id]

    # --- filter eligible Pokémon for the chosen area ---
    def get_eligible_pokemon() -> dict:
        eligible = {}
        for pdata in area["pokemon"]:
            if player_points < pdata["req_points"]:
                continue
            req_game = pdata.get("req_game")
            if req_game == "bw" and not is_bw:
                continue
            if req_game == "b2w2" and not is_b2w2:
                continue
            eligible[pdata["natdex"]] = pdata
        return eligible

    # --- pick one eligible Pokémon from the area ---
    def pick_area_pokemon():
        eligible = get_eligible_pokemon()
        natdex = choice(list(eligible.keys()))
        pdata  = eligible[natdex]

        form_name = pdata.get("form")
        lookup_key = f"{natdex}-{form_name}" if form_name else str(natdex)

        pkmn_entry = pokemon.pokemon_info.get(lookup_key)

        pkmn = {**pkmn_entry, "pokemon_no": natdex}
        return pkmn, pdata

    # --- pick one eligible item from the area ---
    def pick_area_item():
        eligible = [iid for iid, ipoints in area["items"] if player_points >= ipoints]

        item_id = choice(eligible)

        #items do not all show up at the same frequency, but i dont know if we have enough data to determine what the rarities are.
        #its probably at least partially based on the req_points to unlock those items
        return item_id

    # --- Encounter builders ---
    def make_pokemon_encounter(pkmn, pdata, obj_id, obj_pkmn_id, category=0):
        gender_id = choice(pkmn["gender_ratio"])
        gender_key = "m" if gender_id == 0 else "f"

        # Use the gender-specific minigame list
        minigame_pool = pdata["minigames"].get(gender_key)
        minigame_id = 1 if category == 1 else choice(minigame_pool)

        encounter_store[obj_pkmn_id] = {"type": "pokemon", "pokemon": pkmn}
        return {
            "object_id":         obj_id,
            "otoken":            save_data.generate_otoken(),
            "public_date_from":  None,
            "public_date_to":    None,
            "object_category":   category,
            "minigame_id":       minigame_id,
            "kinomi_id":         0,
            "kinomi_count":      0,
            "pokeitem_id":       0,
            "object_pokemon_id": obj_pkmn_id,
            "pokemon": {
                "pokemon_no":  pkmn["pokemon_no"],
                "form_no":     pkmn.get("form_no", 0),
                "pokename":    text.lookup_str("pokemon", pkmn["pokemon_no"]),
                "sex_id":      gender_id,
                "action_type": 1,
                "type1":       text.lookup_str("type", pkmn["type1"]),
                "type2":       text.lookup_str("type", pkmn["type2"]),
                "speabi1":     text.lookup_str("ability", pkmn["speabi1"]),
                "speabi2":     text.lookup_str("ability", pkmn["speabi2"]),
                "speabi3":     text.lookup_str("ability", pkmn["speabi3"])
            }
        }

    def make_item_encounter(item_id, obj_id, obj_pkmn_id):
        encounter_store[obj_pkmn_id] = {"type": "item", "item_id": item_id}
        return {
            "object_id":         obj_id,
            "otoken":            save_data.generate_otoken(),
            "public_date_from":  None,
            "public_date_to":    None,
            "object_category":   2,
            "minigame_id":       0,
            "kinomi_id":         0,
            "kinomi_count":      0,
            "pokeitem_id":       0,
            "object_pokemon_id": obj_pkmn_id,
        }

    # --- Build the object list ---
    object_list       = []
    base_obj_pkmn_id  = randint(3700, 4000)

    # First entry is always the special Pokémon (category 1)
    pkmn, pdata = pick_area_pokemon()
    object_list.append(make_pokemon_encounter(pkmn, pdata, randint(100, 400), base_obj_pkmn_id, category=1))

    for i in range(1, 30):
        obj_id = randint(90, 400)
        base_obj_pkmn_id -= i

        if randint(1, 2) == 1:  # ratio of pokemon/items is about 50/50
            item_id = pick_area_item()
            object_list.append(make_item_encounter(item_id, obj_id, base_obj_pkmn_id))
            continue

        pkmn, pdata = pick_area_pokemon()
        object_list.append(make_pokemon_encounter(pkmn, pdata, obj_id, base_obj_pkmn_id))

    response = {
        "dreamland_area_id": dreamland_area_id,
        "object_list":       object_list,
    }
    return json.dumps(response).encode()


def GET_tree_top(_query):
    count = randint(1, 10)

    pokemon_list = []
    encount_list = []

    for _ in range(count):
        pkmn = pokemon.get_random_pokemon()

        pokemon_list.append({
            "pokemon_no":        pkmn["pokemon_no"],
            "form_no":           pkmn.get("form_no", 0),
            "pgl_name":          "PGLName",
            "member_savedata_id": 123,
            "nickname":          None,
            "pokename":          text.lookup_str("pokemon", pkmn["pokemon_no"]),
            "oyaname":           "PlayerName",
            "level":             randint(1, 100),
            "type1":             text.lookup_str("type", pkmn["type1"]),
            "type2":             text.lookup_str("type", pkmn["type2"]),
            "sex_id":            0,
            "pokekaku":          text.lookup_str("nature", randint(0, 24)),
            "pokeplace":         "Route 1",
            "ball_name":         text.lookup_str("ball", 4)
        }
    )

    response = {"pokemon_list": pokemon_list, "encount_list": encount_list}
    return json.dumps(response).encode()

# ---------------------
# POST API calls
# ---------------------

def POST_game_clear(_query):
    """Handles processing data for collected items and post-minigame Pokémon.

    The result parameter of _query should be used to determine which of the three,
    if any, special moves the Pokémon will have. The better moves are rarer, but
    the exact probabilities are unknown.

    For Pokémon encounters, the following is handled by the server:
        waza_name_disp: Name of the special move
        waza_count: Total number of moves the Pokémon knows

    Args:
        _query: A dict of request parameters. Possible params:
            object_pokemon_id: Used for indexing into encount_list.
            pokeitem_id: Always 0 unless minigame 2 was played (Ice Cream Scoop).
                Will have the item ID of the Berry that was consumed.
            result: MD5 hash of the following:
                Game result (0 if failure/abort, 1-5 if success)
                token
                object_pokemon_id

    Returns:
        A JSON-encoded bytes object representing the reward data.
    """
    print(json.dumps(_query, indent=2))

    encounter = encounter_store[int(_query["object_pokemon_id"])]

    if encounter["type"] == "pokemon":
        pkmn = encounter["pokemon"]

        if len(pkmn["gender_ratio"]) > 1: #DW pokemon are always 66/33 male/female regardless of normal gender ratios
            gender_id = choices([0, 1], weights=[2/3, 1/3], k=1)[0]
        else:
            gender_id = pkmn["gender_ratio"][0]

        reward = {
            "pokemon": {
                "pokemon_no":     pkmn["pokemon_no"],
                "pokename":       text.lookup_str("pokemon", pkmn["pokemon_no"]),
                "form_no":        pkmn.get("form_no", 0),
                "sex_id":         gender_id,
                "waza_name_disp": None if "special_moves" not in pkmn else text.lookup_str("move", choice(pkmn["special_moves"])),
                "waza_count":     4,
                "type1":       text.lookup_str("type", pkmn["type1"]),
                "type2":       text.lookup_str("type", pkmn["type2"]),
                "speabi1":     text.lookup_str("ability", pkmn["speabi1"]),
                "speabi2":     text.lookup_str("ability", pkmn["speabi2"]),
                "speabi3":     text.lookup_str("ability", pkmn["speabi3"])
            },
            "item":     None,
            "interior": None,
            "present":  None,
        }

    #there is an encounter-with-berry branch missing here

    elif encounter["type"] == "item":
        item_id = encounter["item_id"]
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

        managers.chest.add_item(item_id, 1)

    else:
        raise ValueError(f"Unknown encounter type: {encounter['type']}")

    return json.dumps(reward).encode()