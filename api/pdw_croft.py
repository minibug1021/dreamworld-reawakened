import json
import time
from pathlib import Path
from datetime import datetime
from flask import request
from utils import text
from utils import save_data
from utils import managers
from api import pdw_home
from game_sync_server.entralinked.utility.db_manager import db

ROOT_DIR = Path(__file__).resolve().parent.parent

with open(ROOT_DIR / "json_data" / "items.json", encoding="UTF-8") as f:
    item_info = json.load(f)

with open(ROOT_DIR / "json_data" / "berries.json", encoding="UTF-8") as f:
    berry_data = json.load(f)

# ---------------------
# GET API calls
# ---------------------

def GET_my_croft_list(_query):
    return(json.dumps(managers.crops.data).encode())

def GET_friend_croft_list(_query):
    member_id = int(_query.get("member_savedata_id"))
    response = listloader(member_id)
    return(json.dumps(response).encode())



def GET_tutorial_end(_query):
    return b'{}'


def GET_tutorial_start(_query):
    return b'{}'


def GET_waterpot_list(_query):
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

# ---------------------
# POST API calls
# ---------------------

def POST_kinomi_harvesting(_query):
    my_croft_id = int(_query.get("my_croft_id"))

    harvest_result = managers.crops.harvest(my_croft_id)
    managers.chest.add_item(harvest_result["pokeitem_id"], harvest_result["count"])

    return json.dumps(harvest_result).encode()


def POST_kinomi_sowing(_query):
    my_croft_id = int(_query.get("my_croft_id"))
    pokeitem_id = int(_query.get("pokeitem_id"))

    managers.crops.sow(my_croft_id, pokeitem_id)
    managers.chest.remove_item(pokeitem_id, 1)

    return json.dumps(managers.crops.data).encode()


def POST_kinomi_watering(_query):
    my_croft_id = int(_query.get("my_croft_id"))

    managers.crops.water_plot(my_croft_id)

    return json.dumps(managers.crops.data).encode()

def POST_friend_kinomi_watering(_query):
    my_croft_id = int(_query.get("my_croft_id"))

    member_id = int(_query.get("member_savedata_id"))

    water_f_plot(my_croft_id, member_id)
    
    pdw_home.watered_footprint_plot(member_id)   

    c_data = listloader(member_id)

    return json.dumps(c_data).encode()

def POST_waterpot_list(_query):
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

# ---------------------
# Multiplayer Crop Code
# ---------------------

def waterint():
    new_remains_watering = 20
    set_new_remains_water(new_remains_watering)


def listloader(member_id: int):
    c_data = db.f_read(member_id, "crop_data")

    for crop in c_data["croft_list"]:
        if "pokeitem_id" not in crop:
            continue

        berry_desc = text.lookup_str("item_descriptions", crop["pokeitem_id"])

        crop["kinomi"] = text.lookup_str("item", crop["pokeitem_id"])
        crop["kinomi_id"] = crop["pokeitem_id"] - 148

        crop["desc1"] = berry_desc[0]
        crop["desc2"] = berry_desc[1]
        crop["desc3"] = berry_desc[2]

    return c_data

def f_growth(member_id: int):
    c_data = listloader(member_id)
    remains_watering =  db.read(save_data.gscd, "water_cnt")   
    current_time = round(time.time())
    for plant in c_data["croft_list"]:
        if "dirt_hp" not in plant:
            continue

        curr_berry_data = berry_data[str(plant["kinomi_id"])]

        hours_since_planted = (current_time - plant["server"]["planted_at"]) // 3600
        hours_since_update = (current_time - plant["server"]["updated_at"]) // 3600

        hours_at_last_update = hours_since_planted - hours_since_update

        single_stage_time = curr_berry_data["grow_time"] / 4

        for hour in range(1, hours_since_update + 1):
            total_hours = hours_at_last_update + hour
            plant["kinomi_state"] = min(total_hours // single_stage_time, 4)

            if plant["dirt_hp"] == 0: #remove 1/5th of the berry's max, but no lower than 2 berries
                plant["server"]["yield"] = max(plant["server"]["yield"] - (curr_berry_data["max_yield"] * 0.2), 2)
            else:
                plant["dirt_hp"] -= curr_berry_data["drain_rate"]

        if plant["dirt_hp"] < 0:
            plant["dirt_hp"] = 0

        plant["server"]["updated_at"] = current_time

    redundant_fields = {"kinomi", "kinomi_id", "desc1", "desc2", "desc3"}
    crop_data = {
        "croft_list": [
            {k: v for k, v in crop.items() if k not in redundant_fields}
            for crop in c_data["croft_list"]
        ],
        "remains_watering": remains_watering,
        "diglett_flag": 0
    }

    db.f_write(member_id, "crop_data", crop_data)

def fetch_plot_by_id(my_croft_id: int, c_data: dict):
    return next((p for p in c_data["croft_list"] if p["my_croft_id"] == my_croft_id), None)

def water_f_plot(my_croft_id: int, member_id: int):
    c_data = listloader(member_id)
    remains_watering =  db.read(save_data.gscd, "water_cnt")
    plot = fetch_plot_by_id(my_croft_id, c_data)
    plot["dirt_hp"] = 100
    new_remains_watering = remains_watering - 1
    redundant_fields = {"kinomi", "kinomi_id", "desc1", "desc2", "desc3"}

    crop_data = {
        "croft_list": [
            {k: v for k, v in crop.items() if k not in redundant_fields}
            for crop in c_data["croft_list"]
        ],
        "remains_watering": new_remains_watering,
        "diglett_flag": 0
    }

    db.f_write(member_id, "crop_data", crop_data)

    set_new_remains_water(new_remains_watering)

def set_new_remains_water(new_remains_watering: int):

    db.write(save_data.gscd, "water_cnt", new_remains_watering)
