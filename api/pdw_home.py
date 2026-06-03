import json
import psutil
import threading
from zoneinfo import ZoneInfo
from datetime import datetime
from random import choice, randint

from utils import text
from utils import pokemon
from utils import save_data

# ---------------------
# GET API calls
# ---------------------

def GET_board_pokemon_list(_query):
    print(json.dumps(_query, indent=2))

    return b'{}'


def GET_footprint_list(_query):
    footprint_list = {"list":[]}

    valid_footprints = [598,25,85,623,2,32,183,428,648,636,616,609,594,593,574,564,558,547,543,520,518,491,474,421,420,406,121,120,13,10,647]

    for _ in range(10):
        pkmn = pokemon.get_random_pokemon(valid_footprints)
        footprint = {
            "is_pdw": randint(0, 1),
            "is_gts": randint(0, 1),
            "is_ds": randint(0, 1),
            "friend_type": randint(0, 2),
            "updated_at": "2026/05/06 22:00",
            "pokemon_nickname": "pokemon_nickname",
            "pokemon_name": text.lookup_str("pokemon", pkmn["pokemon_no"]),
            "pgl_name": "pgl_name",
            "pokemon_no": pkmn["pokemon_no"],
            "form_no": pkmn.get("form_no", 0), #below this is used for the popup menu
            "oyaname": "oyaname",
            "level": pkmn["level"],
            "type1": text.lookup_str("type", pkmn["type1"]),
            "type2": text.lookup_str("type", pkmn["type2"]),
            "sex_id": choice(pkmn["gender_ratio"]),
            "personality": text.lookup_str("nature", randint(0, 24)),
            "exchange_flag": randint(0, 1),
            "water_flag": randint(0, 1)
        }
        footprint_list["list"].append(footprint)

    return json.dumps(footprint_list).encode()


def GET_my_bridge(_query):
    return b'{}'


def GET_my_island(_query):
    pkmn = pokemon.sleeping_pokemon

    response = {
        "pokemon":                 {**pkmn},
        "island_id":               201,
        "point":                   0,
        "trial_flag":              0,
        "arranged_interior_list":  [{"my_interior_id":1,"interior_id":1,"x":10,"y":10,"interior_size":1,"interior_category_id":1,"rotation":0}],
        "requested_flag":          False,
        "shelf_id":                301
    }
    return json.dumps(response).encode()


def GET_my_island_area(_query):
    player_data = save_data.read_player_data()

    friend_list = []
    for _ in range(5):
        friend = {
            "pgl_name": "OtherPlayerName",
            "member_id": randint(1,50000),
            "member_savedata_id": randint(1,50000),
            "island_id": 201,
            "country_id": 176,
            "is_ds": randint(0, 1),
            "is_gts": randint(0, 1),
            "is_pdw": randint(0, 1)
        }
        friend_list.append(friend)
    response = {
        "island_id": player_data["member"]["island_id"],
        "friend_list": friend_list
    }

    return(json.dumps(response).encode())


def GET_pdw_end(_query):
    save_data.update_gamesync_status(save_data.PlayerStatus.WAKE_READY)

    for proc in psutil.process_iter():
        if "flashplayer" in proc.name():
            threading.Timer(2.5, proc.kill).start()

    return b'{}'

# ---------------------
# POST API calls
# ---------------------

def POST_pdw_start(_query):
    now_local = datetime.now().astimezone()
    now_japan = now_local.astimezone(ZoneInfo("Asia/Tokyo"))

    pokemon_no = save_data.read_player_data()["member"]["pokemon_no"]

    data = {
        "last_started_at": int(now_japan.timestamp()),
        "last_logined_at": int(now_japan.timestamp()),
        "last_started_at_timezone": int(now_local.timestamp()),
        "pokemon_name": text.lookup_str("pokemon", pokemon_no)
    }

    save_data.write_player_data(data)

    pkmn = pokemon.sleeping_pokemon

    species_name = text.lookup_str("pokemon", pkmn["pokemon_no"])

    pkmn_data = {
        "pokemon_no":       pkmn["pokemon_no"],
        "pokemon_name":     species_name,
        "form_no":          pkmn["form_no"],
        "type1":            text.lookup_str("type", pkmn["type1"]),
        "type2":            text.lookup_str("type", pkmn["type2"]),
        "pokemon_nickname": pkmn["pokemon_nickname"] if pkmn["pokemon_nickname"] != species_name else None,
        "oyaname":          pkmn["oyaname"],
        "level":            pkmn["level"],
        "sex":              pkmn["sex"],
        "personality":      text.lookup_str("nature", pkmn["personality"]),
        "ball_name":        text.lookup_str("ball", pkmn["ball_name"]),
    }

    pokemon.sleeping_pokemon = pkmn_data

    response = {"started_at":int(now_local.timestamp())}
    return json.dumps(response).encode()


def POST_pdw_timecheck(_query):
    return b'{}'
