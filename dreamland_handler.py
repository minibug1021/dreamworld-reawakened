#!/usr/bin/env python3
import json
import logging
from random import choice
from random import choices
from random import randint

import game_data

encounter_store = {}

def handle_dreamland_top(_query):
    if _query["is_random"]:
        object_list = []
        for _ in range(10):
            pkmn = game_data.get_random_pokemon()
            
            object_list.append(
                {
                "object_id": randint(1, 1000),
                "object_category": randint(0, 1),
                "pokemon": {
                    "pokemon_no": pkmn["pokemon_no"],
                    "form_no": pkmn.get("form_no", "0"),
                    "pokename": pkmn["pokemon_name"]
                },
                "minigame_id": choice([1, 2, 3, 4, 6, 8, 9, 10, 12]),
                "kinomi_id": 0,
                "kinomi_count": 0,
                "pokeitem_id": 0,
                "object_pokemon_id": 0,
                "otoken": game_data.generate_otoken()
                }
            )
        response = {
            "dreamland_area_id": randint(3, 9),
            "object_list": object_list
        }
        return json.dumps(response).encode()

    # --- get player game version ---
    rom_name      = game_data.player_data["member"]["rom_name"]
    player_points = int(game_data.player_data["member"]["point"])
    player_badges = int(game_data.player_data["member"]["player_badge_num"])
    player_types  = {game_data.player_data["member"]["type1"], game_data.player_data["member"]["type2"]}

    is_bw   = rom_name in ("Pokémon Black Version", "Pokémon White Version")
    is_b2w2 = rom_name in ("Pokémon Black Version 2", "Pokémon White Version 2")
    game_key = "bw" if is_bw else "b2w2"

    # --- select eligible Dream Island area ---
    eligible_areas = []
    area_weights   = []
    for area_id, area in game_data.area_info.items():
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

    area = game_data.area_info[dreamland_area_id]

    # --- filter eligible Pokémon for the chosen area ---
    def get_eligible_pokemon() -> dict:
        eligible = {}
        for natdex, pdata in area["pokemon"].items():
            if player_points < pdata["req_points"]:
                continue
            req_game = pdata.get("req_game")
            if req_game == "bw" and not is_bw:
                continue
            if req_game == "b2w2" and not is_b2w2:
                continue
            eligible[natdex] = pdata
        return eligible

    # --- pick one eligible Pokémon from the area ---
    def pick_area_pokemon():
        eligible = get_eligible_pokemon()
        natdex = choice(list(eligible.keys()))
        pdata  = eligible[natdex]
        pkmn_entry = game_data.pokemon_info.get(natdex)

        pkmn = {**pkmn_entry, "pokemon_no": natdex}
        return pkmn, pdata

    # --- pick one eligible item from the area ---
    def pick_area_item():
        eligible = [iid for iid, idata in area["items"].items()
                    if player_points >= idata["req_points"]]

        item_id = choice(eligible)

        #items do not all show up at the same frequency, but i dont know if we have enough data to determine what the rarities are.
        #its probably at least partially based on the req_points to unlock those items
        return item_id

    # --- Encounter builders ---
    def make_pokemon_encounter(pkmn, pdata, obj_id, obj_pkmn_id, category="0"):
        gender_id = choice(pkmn["gender_ratio"])
        gender_key = "male" if gender_id == 0 else "female"

        # Use the gender-specific minigame list
        minigame_pool = pdata["minigames"].get(gender_key)
        minigame_id = "1" if category == "1" else str(choice(minigame_pool))

        encounter_store[str(obj_pkmn_id)] = {"type": "pokemon", "pokemon": pkmn}
        return {
            "object_id":         str(obj_id),
            "otoken":            game_data.generate_otoken(),
            "public_date_from":  None,
            "public_date_to":    None,
            "object_category":   category,
            "minigame_id":       minigame_id,
            "kinomi_id":         "0",
            "kinomi_count":      "0",
            "pokeitem_id":       0,
            "object_pokemon_id": obj_pkmn_id,
            "pokemon": {
                "pokemon_no":  pkmn["pokemon_no"],
                "form_no":     pkmn.get("form_no", "0"),
                "pokename":    pkmn["pokemon_name"],
                "sex_id":      str(gender_id),
                "action_type": "1",
                "type1":       pkmn["type1"],
                "type2":       pkmn.get("type2", ""),
                "speabi1":     pkmn["speabi1"],
                "speabi2":     pkmn.get("speabi2", ""),
                "speabi3":     pkmn["speabi3"],
            }
        }

    def make_item_encounter(item_id, obj_id, obj_pkmn_id):
        encounter_store[str(obj_pkmn_id)] = {"type": "item", "item_id": item_id}
        return {
            "object_id":         str(obj_id),
            "otoken":            game_data.generate_otoken(),
            "public_date_from":  None,
            "public_date_to":    None,
            "object_category":   "2",
            "minigame_id":       "0",
            "kinomi_id":         "0",
            "kinomi_count":      "0",
            "pokeitem_id":       0,
            "object_pokemon_id": obj_pkmn_id,
        }

    # --- Build the object list ---
    object_list       = []
    base_obj_pkmn_id  = randint(3700, 4000)

    # First entry is always the special Pokémon (category 1)
    pkmn, pdata = pick_area_pokemon()
    object_list.append(make_pokemon_encounter(pkmn, pdata, randint(100, 400), base_obj_pkmn_id, category="1"))

    for i in range(1, 10):
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


def handle_dreamland_tree_top(_query):
    count = randint(1, 10)

    pokemon_list = []
    encount_list = []
    
    for _ in range(count):
        pkmn = game_data.get_random_pokemon()

        pokemon_list.append({
            "pokemon_no":        pkmn["pokemon_no"],
            "form_no":           pkmn.get("form_no", "0"),
            "pgl_name":          "PGLName",
            "member_savedata_id": 123,
            "nickname":          None,
            "pokename":          pkmn["pokemon_name"],
            "oyaname":           "PlayerName",
            "level":             randint(1, 100),
            "type1":             pkmn["type1"],
            "type2":             pkmn["type2"],
            "sex_id":            0,
            "pokekaku":          choice(game_data.pokemon_natures),
            "pokeplace":         "Route 1",
            "ball_name":         "Poke Ball"
        }
    )   

    encount_list = []
    
    response = {"pokemon_list": pokemon_list, "encount_list": encount_list}
    logging.info("tree_top response: %s", json.dumps(response))
    return json.dumps(response).encode()


def handle_game_clear(_query):
    encounter = encounter_store.get(str(_query["object_pokemon_id"][0]))

    if encounter["type"] == "pokemon":
        pkmn = encounter["pokemon"]
        reward = {
            "pokemon": {
                "pokemon_no":     pkmn["pokemon_no"],
                "pokename":       pkmn["pokemon_name"],
                "form_no":        pkmn.get("form_no", "0"),
                "gender_id":      str(randint(0, 1)),
                "waza_name_disp": "Sunny Day" if "special_moves" not in pkmn else choice(pkmn["special_moves"])["move_name"],
                "waza_count":     4,
                "action_type":    "1",
                "type1":          pkmn["type1"],
                "type2":          pkmn.get("type2", ""),
                "speabi1":        pkmn["speabi1"],
                "speabi2":        pkmn.get("speabi2", ""),
                "speabi3":        pkmn["speabi3"],
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
                "pokeitem_id":   int(item_id),
                "pokeitem":      game_data.item_info[item_id]["item_name"],
                "poke_item_num": 1,
            },
            "interior": None,
            "present":  None,
        }
 
    logging.info("game_clear response: %s", json.dumps(reward))
    return json.dumps(reward).encode()