#!/usr/bin/env python3
import time
import json
from random import choice
from random import randint

import game_data

from dreamland_handler import handle_dreamland_top, handle_dreamland_tree_top, handle_game_clear

# --------------------
# Static API responses
# --------------------

STATIC_GET_RESPONSES = {
    "pgl.news.information_list":   json.dumps({"list":[], "total_count":0}).encode(),
    "pgl.member.profile.my_state": b"{}",
    "pgl.top.init":                b"{}",
    "pdw.home.my_bridge":          b"{}",
    "pdw.croft.tutorial_start":    b"{}",
    "pdw.croft.tutorial_end":      b"{}",
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


def handle_item_list(_query):
    item_kind_id = int(_query.get("item_kind_id", [0])[0])
    sort_key = int(_query.get("sort_key", [3])[0])

    if item_kind_id == 0: #all items
        item_list = game_data.chest_data["list"]
    elif item_kind_id == 1: #only berries
        item_list = [item for item in game_data.chest_data["list"] if int(item["pokeitem_id"]) in range(149, 213)]

    if sort_key == 1: #date
        item_list = sorted(item_list, key=lambda x: game_data.date_to_unix(x["date"]), reverse=True)
    elif sort_key == 2: #type
        item_list = sorted(
            item_list,
            key=lambda x: (
                int(x["bunrui_no"]),
                int(x["b_hozon_sentou"])
            )
        )
    elif sort_key == 3: #name
        item_list = sorted(item_list, key=lambda x: x["pokeitem"])

    return json.dumps({"cnt": len(item_list), "list": item_list}).encode()


def handle_my_island(_query):
    if _query["is_random"]:
        pkmn = game_data.get_random_pokemon()
    else:
        pkmn = game_data.player_data["member"]

    response = {
        "pokemon": {
            "pokemon_no":        pkmn["pokemon_no"],
            "pokemon_name":      pkmn["pokemon_name"],
            "form_no":           pkmn.get("form_no", "0"),
            "type1":             pkmn["type1"],
            "type2":             pkmn["type2"],
            "pokemon_nickname":  None,
            "oyaname":           pkmn.get("alter_rom_name", game_data.player_data["member"]["pgl_name"]),
            "level":             randint(1, 100),
            "sex":               randint(0, 1),
            "personality":       choice(game_data.pokemon_natures),
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

def handle_footprint_list(_query):
    footprint_list = {"list":[]}

    valid_footprints = [598,25,85,623,2,32,183,428,648,636,616,609,594,593,574,564,558,547,543,520,518,491,474,421,420,406,121,120,13,10,647]

    for _ in range(10):
        footprint = {
            "is_pdw": 1,
            "is_gts": 0,
            "is_ds": 0,
            "friend_type": 0,
            "updated_at": "2026/05/06 22:00",
            "pokemon_nickname": "pokemon_nickname",
            "pokemon_name": "pokemon_name",
            "pgl_name": "pgl_name",
            "alter_rom_name": "alter_rom_name",
            "pokemon_no": choice(valid_footprints),
            "form_no": "0"
        }
        footprint_list["list"].append(footprint)

    return json.dumps(footprint_list).encode()

def handle_croft_list(_query):
    return(json.dumps(game_data.crop_data).encode())

# --------

def handle_kinomi_sowing(_query):
    my_croft_id = int(_query.get("my_croft_id")[0])
    pokeitem_id = _query.get("pokeitem_id")[0]
    
    for plant in game_data.crop_data["croft_list"]:
        if plant["my_croft_id"] == my_croft_id:
            break

    current_time = round(time.time())
    berry_id = int(pokeitem_id) - 148

    plant.update({
        "my_croft_id": my_croft_id,
        "pokeitem_id": int(pokeitem_id),
        "kinomi": game_data.item_info[pokeitem_id]["item_name"],
        "kinomi_id": berry_id,
        "dirt_hp": 100,
        "desc1": game_data.item_info[pokeitem_id]["desc"][0],
        "desc2": game_data.item_info[pokeitem_id]["desc"][1],
        "desc3": game_data.item_info[pokeitem_id]["desc"][2],
        "kinomi_state": 0,
        "x": plant["x"],
        "y": plant["y"],
        "server": {"planted_time": current_time, "last_update_time": current_time, "yield": game_data.berry_data[str(berry_id)]["max_yield"]}
    })

    game_data.save_crops()

    return json.dumps(game_data.crop_data).encode()


def handle_kinomi_watering(_query):
    my_croft_id = int(_query.get("my_croft_id")[0])

    for plant in game_data.crop_data["croft_list"]:
        if plant["my_croft_id"] == my_croft_id:
            break

    plant["dirt_hp"] = 100

    game_data.save_crops()

    return json.dumps(game_data.crop_data).encode()


def handle_kinomi_harvesting(_query):
    my_croft_id = int(_query.get("my_croft_id")[0])

    for index, plant in enumerate(game_data.crop_data["croft_list"]):
        if plant["my_croft_id"] == my_croft_id:
            break

    for item in game_data.chest_data["list"]:
        item["item_cnt"] += plant["server"]["yield"]

    response = {
        "kinomi_id": plant["kinomi_id"],
        "kinomi": plant["kinomi"],
        "pokeitem_id": plant["pokeitem_id"],
        "count": plant["server"]["yield"]
    }

    game_data.crop_data["croft_list"][index] = {
        "my_croft_id": plant["my_croft_id"],
        "x": plant["x"],
        "y": plant["y"]
    }

    game_data.save_crops()
    game_data.save_treasure_chest()

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
    "pdw.croft.waterpot_list":   handle_waterpot_list_GET,
    "pdw.dreamland.top":         handle_dreamland_top,
    "pdw.dreamland.tree_top":    handle_dreamland_tree_top,
    "pdw.item.item_list":        handle_item_list,
    "pdw.home.my_island":        handle_my_island,
    "pdw.home.footprint_list":   handle_footprint_list,
    "pdw.croft.my_croft_list":   handle_croft_list
}

DYNAMIC_POST_RESPONSES = {
    "pdw.dreamland.game_clear":    handle_game_clear,
    "pdw.croft.kinomi_sowing":     handle_kinomi_sowing,
    "pdw.croft.kinomi_watering":   handle_kinomi_watering,
    "pdw.croft.kinomi_harvesting": handle_kinomi_harvesting,
    "pdw.croft.waterpot_list":     handle_waterpot_list_POST,
}