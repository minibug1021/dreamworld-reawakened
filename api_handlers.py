#!/usr/bin/env python3
import time
import json
import logging
from random import randint
from random import choice
from pathlib import Path

# --------------------
# Pokemon related data
# --------------------

ROOT_DIR = Path(__file__).resolve().parent

with open(ROOT_DIR / "json_data" / "player_data.json") as f:
    player_data = json.load(f)

with open(ROOT_DIR / "json_data" / "items.json") as f:
    item_info = json.load(f)

with open(ROOT_DIR / "json_data" / "pokemon.json") as f:
    pokemon_info = json.load(f)

pokemon_natures = ("Adamant","Bashful","Bold","Brave","Calm","Careful","Docile","Gentle","Hardy","Hasty","Impish","Jolly","Lax","Lonely","Mild","Modest","Naive","Naughty","Quiet","Quirky","Rash","Relaxed","Sassy","Serious","Timid")

# --------------------
# Helper functions
# --------------------

def get_random_pokemon() -> dict[str: str|None]:
    pkmn = choice(list(pokemon_info.keys()))
    natdex = pkmn.split("-")[0]

    return {**pokemon_info[pkmn], "pokemon_no": natdex}

# --------------------
# Static API responses
# --------------------

STATIC_GET_RESPONSES = {
    "pgl.news.information_list":   json.dumps({"list":[], "total_count":0}).encode,
    "pgl.member.profile.my_state": b"{}",
    "pgl.top.init":                b"{}",
    "pdw.home.my_bridge":          b"{}",
    "pdw.croft.tutorial_start":    b"{}",
    "pdw.croft.tutorial_end":      b"{}",
    "pdw.home.footprint_list":     b"{}",
}

STATIC_POST_RESPONSES = {
    "pdw.home.pdw_timecheck":        b"{}",
    "pgl.member.profile.pdw_login":  b"{}",
    "pdw.item.item_trade_list":      json.dumps([{"material_id":None,"item_id":None,"pokeitem":None,"x":1,"y":1,"history_id":None,"old_member_savedata_id":None,"pokemon_no":None,"form_no":None,"pokename":None,"pgl_name":None,"nickname":None,"poke_nickname":None,"field_line1":None,"field_line2":None,"field_line3":None,"created_at":"","old_item_id":None,"new_item_id":None,"old_item_name":None}]).encode(),
    "pdw.home.pdw_start":            json.dumps({"started_at": int(time.time())}).encode(),
}

# ---------------------
# Dynamic API responses
# ---------------------

def handle_my_croft_list(_query):
    croft_template = {
      "pokeitem_id": None,
      "kinomi": None,
      "kinomi_id": None,
      "dirt_hp": 100,
      "kinomi_state": 0,
    }
    response = {
        "croft_list": [
            {"my_croft_id": 1000, **croft_template, "x": 1, "y": 1},
            {"my_croft_id": 1001, **croft_template, "x": 2, "y": 1},
            {"my_croft_id": 1002, **croft_template, "x": 3, "y": 1},
            {"my_croft_id": 1003, **croft_template, "x": 1, "y": 2},
            {"my_croft_id": 1004, **croft_template, "x": 2, "y": 2},
            {"my_croft_id": 1005, **croft_template, "x": 3, "y": 2},
        ],
        "diglett_flag": 0,
    }
    print(response)
    return json.dumps(response).encode()


def handle_waterpot_list_GET(_query):
    response = {
        "waterpot_list": [
            {
            "my_interior_id": 283,
            "interior_id": 1,
            "selected_flag": 1,
            "interior_name": "ふつうのじょうろ"
            },
            {
            "my_interior_id": 284,
            "interior_id": 2,
            "selected_flag": 0,
            "interior_name": "ふつうのじょうろ"
            }
        ]
    }

    return json.dumps(response).encode()


def handle_dreamland_top(_query):
    object_list = []
    for _ in range(10):
        pkmn = get_random_pokemon()
        
        object_list.append(
            {
            "object_id": randint(1, 1000),
            "object_category": randint(0, 1), # 0 - Pokemon, 1 - Pokemon Stay, 2 - Item
            "pokemon": {
                "pokemon_no": pkmn["pokemon_no"],
                "form_no": pkmn.get("form_no", "0"),
                "pokename": pkmn["pokemon_name"]
            },
            "minigame_id": choice([3, 4, 6, 8, 9, 10, 12]),
            "kinomi_id": 0,
            "kinomi_count": 0,
            "pokeitem_id": 0,
            "object_pokemon_id": 0,
            "otoken": randint(1, 1000)
            }
        )
    response = {
        "dreamland_area_id": randint(3, 9),
        "object_list": object_list
    }
    return json.dumps(response).encode()


def handle_dreamland_tree_top(_query):
    count = randint(1, 10)

    pokemon_list = []
    encount_list = []
    
    for _ in range(count):
        pkmn = get_random_pokemon()

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
            "pokekaku":          choice(pokemon_natures),
            "pokeplace":         "Route 1",
            "ball_name":         "Poke Ball"
        }
    )   

    encount_list = []
    
    response = {"pokemon_list": pokemon_list, "encount_list": encount_list}
    logging.info("tree_top response: %s", json.dumps(response))
    return json.dumps(response).encode()


def handle_item_list(_query):
    """Loads random items into the Treasure Chest"""
    item_list = []
    for _ in range(randint(1, 10)):
        item_id = choice(list(item_info.keys()))
        item_name = item_info.get(item_id, "TODO")["item_name"]
        item_list.append(
            {
                "pokeitem_id": int(item_id),
                "pokeitem": item_name,
                "item_cnt": str(randint(1, 99)),
                "bunrui_no": "1", #for sorting
                "b_hozon_sentou": "1", #for sorting
                "date": "2026-05-03"
            }
        )
    response = {"cnt": str(len(item_list)), "list": item_list}
    return json.dumps(response).encode()


def handle_my_island(_query):
    if _query["is_random"]:
        pkmn = get_random_pokemon()
    else:
        pkmn = player_data["member"]

    response = {
        "pokemon": {
            "pokemon_no":        pkmn["pokemon_no"],
            "pokemon_name":      pkmn["pokemon_name"],
            "form_no":           pkmn.get("form_no", "0"),
            "type1":             pkmn["type1"],
            "type2":             pkmn["type2"],
            "pokemon_nickname":  None,
            "oyaname":           pkmn.get("alter_rom_name", player_data["member"]["pgl_name"]),
            "level":             randint(1, 100),
            "sex":               randint(0, 1),
            "personality":       choice(pokemon_natures),
            "place":             "PlayerName\"s Island",
            "ball_name":         "Poke Ball"
        },
        "island_id":               201,
        "point":                   0,
        "trial_flag":              0,
        "arranged_interior_list":  [{"my_interior_id":1,"interior_id":1,"x":10,"y":10,"interior_size":1,"interior_category_id":1,"rotation":0}],
        "requested_flag":          False,
        "shelf_id":                301
    }
    return json.dumps(response).encode()


def handle_waterpot_list_POST(_query):
    response = {
        "waterpot_list": [
            {
            "my_interior_id": 283,
            "interior_id": 1,
            "selected_flag": 1,
            "interior_name": "Watering Can"
            }
        ]
    }
    return json.dumps(response).encode()


DYNAMIC_GET_RESPONSES = {
    "pdw.croft.my_croft_list":   handle_my_croft_list,
    "pdw.croft.waterpot_list":   handle_waterpot_list_GET,
    "pdw.dreamland.top":         handle_dreamland_top,
    "pdw.dreamland.tree_top":    handle_dreamland_tree_top,
    "pdw.item.item_list":        handle_item_list,
    "pdw.home.my_island":        handle_my_island,
}

DYNAMIC_POST_RESPONSES = {
    "pdw.croft.waterpot_list": handle_waterpot_list_POST
}