import json
from zoneinfo import ZoneInfo
from datetime import datetime
from random import choice, randint
from api import pdw_croft
from utils import text
from utils import pokemon
from utils import save_data
from utils import managers
from game_sync_server.entralinked.utility.db_manager import db

# ---------------------
# GET API calls
# ---------------------

def GET_board_pokemon_list(_query):
    print(json.dumps(_query, indent=2))

    return b'{}'


def GET_footprint_list(_query):
    print_list =  db.read(save_data.gscd, "footprint_list")

    return json.dumps(print_list).encode()


def GET_my_bridge(_query):
    return b'{}'


def GET_my_island(_query):
    pkmn = pokemon.sleeper

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
    f_list_data =  db.read(save_data.gscd, "friend_data")
    f_list = f_list_data["friend_list"][:4]
    member_id = db.rand_id_read()
    rand_player_data = db.f_read(member_id, "player_data")
    rand_player = rand_player_data["member"]
    rand_player_pgl_name = rand_player["pgl_name"]

    friend_list = []
    for _ in range(1):
        random_player = {
            "pgl_name": rand_player_pgl_name,
            "member_id": rand_player["member_id"],
            "member_savedata_id": rand_player["member_savedata_id"],
            "island_id": rand_player["island_id"],
            "country_id": rand_player["country_id"]
        }

        friend_list.append(random_player)
    print(f_list)
    response = {
        "island_id": player_data["member"]["island_id"],
        "friend_list": friend_list + f_list
    }
    return(json.dumps(response).encode())

def GET_friend_island(_query):
    pkmn = pokemon.sleeper

    f_list =  db.read(save_data.gscd, "friend_data")

    member_id = int(_query.get("friend_member_savedata_id"))

    add_footprint_plot(member_id)

    friend = fetch_friend_by_id(member_id)

    if friend is not None:
        f_status = friend["friend_status"]

    else:

        f_status = 0


    f_pkmn = db.f_read(member_id, "sleeping_pokemon")

    species_name = text.lookup_str("pokemon", f_pkmn["pokemon_no"])

    f_pkmn_data = {
        "pokemon_no":       f_pkmn["pokemon_no"],
        "pokemon_name":     species_name,
        "form_no":          f_pkmn["form_no"],
        "type1":            text.lookup_str("type", f_pkmn["type1"]),
        "type2":            text.lookup_str("type", f_pkmn["type2"]),
        "pokemon_nickname": f_pkmn["pokemon_nickname"],
        "oyaname":          f_pkmn["oyaname"],
        "level":            f_pkmn["level"],
        "sex":              f_pkmn["sex"],
        "personality":      text.lookup_str("nature", f_pkmn["personality"]),
        "ball_name":        text.lookup_str("ball", f_pkmn["ball_name"]),
    }

    pdw_croft.f_growth(member_id)

    response = {
        "pokemon":                 {**pkmn},
        "friend_pokemon":          {**f_pkmn_data},
        "island_id":               201,
        "friend_status":           f_status,
        "point":                   0,
        "trial_flag":              0,
        "arranged_interior_list":  [{"my_interior_id":1,"interior_id":1,"x":10,"y":10,"interior_size":1,"interior_category_id":1,"rotation":0}],
        "requested_flag":          False,
        "shelf_id":                301
    }
    return json.dumps(response).encode()


def GET_friend_island_area(_query):
    player_data = save_data.read_player_data()
    member_id = int(_query.get("friend_member_savedata_id"))
    f_friend_data = db.f_read(member_id, "friend_data")

    response = {
        "island_id": player_data["member"]["island_id"],
        "friend_list": f_friend_data["friend_list"]
    }

    return(json.dumps(response).encode())


def GET_pdw_end(_query):
    save_data.update_gamesync_status(save_data.PlayerStatus.WAKE_READY)

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

    pkmn = db.read(save_data.gscd, "sleeping_pokemon")

    species_name = text.lookup_str("pokemon", pkmn["pokemon_no"])

    pkmn_data = {
        "pokemon_no":       pkmn["pokemon_no"],
        "pokemon_name":     species_name,
        "form_no":          pkmn["form_no"],
        "type1":            text.lookup_str("type", pkmn["type1"]),
        "type2":            text.lookup_str("type", pkmn["type2"]),
        "pokemon_nickname": pkmn["pokemon_nickname"],
        "oyaname":          pkmn["oyaname"],
        "level":            pkmn["level"],
        "sex":              pkmn["sex"],
        "personality":      text.lookup_str("nature", pkmn["personality"]),
        "ball_name":        text.lookup_str("ball", pkmn["ball_name"]),
    }

    pokemon.sleeper = pkmn_data

    response = {"started_at":int(now_local.timestamp())}
    return json.dumps(response).encode()


def POST_pdw_timecheck(_query):
    return b'{}'

def POST_friend_request(_query):
    member_id = int(_query.get("friend_member_savedata_id"))

    friend_data = db.f_read(member_id, "player_data")

    player = save_data.read_player_data()["member"]

    p_f_data = db.read(save_data.gscd, "friend_data")

    f_p_data = db.f_read(member_id, "friend_data")

# p_f_data saves in YOUR db and f_p_data saves in the OTHER player's db

    friend = friend_data["member"]
   
    play_country_id = player["country_id"]

    if play_country_id is not None:

        p_country_id = player["country_id"]

    else:
        p_country_id = 999

    friend_country_id = friend["country_id"]

    if friend_country_id is not None:

        f_country_id = friend["country_id"]

    else:
        f_country_id = 999

    player_data = {
      "pgl_name": player["pgl_name"],
      "avator_id": player["avator_id"],
      "friend_id": player["member_id"],
      "member_id": player["member_id"],
      "member_savedata_id": player["member_savedata_id"],
      "friend_status": 2,
      "island_id": player["island_id"],
      "country_id": p_country_id,
      "is_ds": 0,
      "is_gts": 0,
      "is_pdw": 0
    }

    friend_data = {
      "pgl_name": friend["pgl_name"],
      "avator_id": friend["avator_id"],
      "friend_id": friend["member_id"],
      "member_id": friend["member_id"],
      "member_savedata_id": friend["member_savedata_id"],
      "friend_status": 1,
      "island_id": friend["island_id"],
      "country_id": f_country_id,
      "is_ds": 0,
      "is_gts": 0,
      "is_pdw": 0
    }

    p_f_data["friend_list"].append(friend_data)

    f_p_data["friend_list"].append(player_data)
 
    redundant_fields = {"share_id"}
    fri_data = {
        "friend_list": [
            {k: v for k, v in item.items() if k not in redundant_fields}
            for item in p_f_data["friend_list"]
        ]
    }
    db.write(save_data.gscd, "friend_data", fri_data)

    pla_data = {
        "friend_list": [
            {k: v for k, v in item.items() if k not in redundant_fields}
            for item in f_p_data["friend_list"]
        ]
    }
    db.f_write(member_id, "friend_data", pla_data)
    
    friend_footprint_plot(member_id)

    response = {
        "friend_list": p_f_data["friend_list"]
    }

    return(json.dumps(response).encode())

def POST_friend_accept(_query):
    member_id = int(_query.get("visitor_member_savedata_id"))

    friend_data = db.f_read(member_id, "player_data")

    player = save_data.read_player_data()["member"]

    p_member_id = player["member_id"]

    p_f_data = db.read(save_data.gscd, "friend_data")

    f_p_data = db.f_read(member_id, "friend_data")

# p_f_data saves in YOUR db and f_p_data saves in the OTHER player's db

    friend = friend_data["member"]

    play_country_id = player["country_id"]

    if play_country_id is not None:

        p_country_id = player["country_id"]

    else:
        p_country_id = 999

    friend_country_id = friend["country_id"]

    if friend_country_id is not None:

        f_country_id = friend["country_id"]

    else:
        f_country_id = 999

    f_fetch = fetch_friend_by_id(member_id)

    f_index = p_f_data["friend_list"].index(f_fetch)

    p_fetch = fetch_player_by_id(member_id, p_member_id)

    p_index = f_p_data["friend_list"].index(p_fetch)

    f_p_data["friend_list"][p_index] = {
      "pgl_name": player["pgl_name"],
      "avator_id": player["avator_id"],
      "friend_id": friend["member_id"],
      "member_id": player["member_id"],
      "member_savedata_id": player["member_savedata_id"],
      "friend_status": 3,
      "island_id": player["island_id"],
      "country_id": p_country_id,
      "is_ds": 0,
      "is_gts": 0,
      "is_pdw": 1
    }

    p_f_data["friend_list"][f_index] = {
      "pgl_name": friend["pgl_name"],
      "avator_id": friend["avator_id"],
      "friend_id": friend["member_id"],
      "member_id": friend["member_id"],
      "member_savedata_id": friend["member_savedata_id"],
      "friend_status": 3,
      "island_id": friend["island_id"],
      "country_id": f_country_id,
      "is_ds": 0,
      "is_gts": 0,
      "is_pdw": 1
    }

    redundant_fields = {"share_id"}

    fri_data = {
        "friend_list": [
            {k: v for k, v in item.items() if k not in redundant_fields}
            for item in p_f_data["friend_list"]
        ]
    }
    db.write(save_data.gscd, "friend_data", fri_data)

    pla_data = {
        "friend_list": [
            {k: v for k, v in item.items() if k not in redundant_fields}
            for item in f_p_data["friend_list"]
        ]
    }
    db.f_write(member_id, "friend_data", pla_data)

    friend_footprint_plot(member_id)
    response = {
        "friend_list": p_f_data["friend_list"]
    }
   
    return(json.dumps(response).encode())

# ---------------------
# Friend List Index code
# ---------------------

def fetch_friend_by_id(member_id: int):
    friend_fetch = db.read(save_data.gscd, "friend_data")
    return next((p for p in friend_fetch["friend_list"] if p["member_id"] == member_id), None)

def fetch_player_by_id(member_id: int, p_member_id: int):
    player_fetch = db.f_read(member_id, "friend_data")
    return next((p for p in player_fetch["friend_list"] if p["member_id"] == p_member_id), None)

# ---------------------
# Footprint list code
# ---------------------

def fetch_player_footprint_plot(member_id: int, p_member_id: int):
    print_fetch = db.f_read(member_id, "footprint_list")
    return next((p for p in print_fetch["list"] if p["visitor_member_savedata_id"] == p_member_id), None)

def fetch_friend_footprint_plot(member_id: int):
    print_fetch = db.read(save_data.gscd, "footprint_list")
    return next((p for p in print_fetch["list"] if p["visitor_member_savedata_id"] == member_id), None)

def add_footprint_plot(member_id: int):
    p_data = db.read(save_data.gscd, "player_data")
    r_p_data = p_data["member"]
    p_member_id = r_p_data["member_id"]
    f_p_data = db.f_read(member_id, "friend_data")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    pkmn = db.read(save_data.gscd, "sleeping_pokemon")
    player_spot = fetch_player_by_id(member_id, p_member_id)
    
    if player_spot is not None:
        player = f_p_data["friend_list"].index(player_spot)
        p_fs = f_p_data["friend_list"][player]["friend_status"]

        if p_fs > 1:
            if p_fs == 3:
                friend_type = 2
                is_pdw = 1
            else:
                friend_type = 1
                is_pdw = 0
        else:
            friend_type = 0
            is_pdw = 0 
    else:
        friend_type = 0
        is_pdw = 0

    print_list = db.f_read(member_id, "footprint_list")
    index_print = fetch_player_footprint_plot(member_id, p_member_id)

    if index_print is not None:
        player_print_fetch = print_list["list"].index(index_print)
        player_print = print_list["list"][player_print_fetch]
        print_list["list"][player_print_fetch] = {
            "pgl_name": r_p_data["pgl_name"],
            "island_id": r_p_data["island_id"],
            "country_id": r_p_data["country_id"],
            "visitor_member_savedata_id": p_member_id,
            "friend_type": friend_type,
            "updated_at": current_time,
            "pokemon_nickname": pkmn["pokemon_nickname"],
            "pokemon_name": text.lookup_str("pokemon", pkmn["pokemon_no"]),
            "pokemon_no": pkmn["pokemon_no"],
            "form_no": pkmn.get("form_no", 0),
            "oyaname": pkmn["oyaname"],
            "level": pkmn["level"],
            "sex_id": pkmn["sex"],
            "personality": text.lookup_str("nature", pkmn["personality"]),
            "type1": text.lookup_str("type", pkmn["type1"]),
            "type2": text.lookup_str("type", pkmn["type2"]),
            "is_pdw": is_pdw,
            "is_gts": player_print["is_gts"],
            "is_ds": player_print["is_ds"],
            "exchange_flag": 0,
            "water_flag": 0
        }
        redundant_fields = {"kinomi", "kinomi_id"}
        print_data = {
            "list": [
                {k: v for k, v in item.items() if k not in redundant_fields}
                for item in print_list["list"]
            ]
        }

        db.f_write(member_id, "footprint_list", print_data)
    else:
        footprint = {
            "pgl_name": r_p_data["pgl_name"],
            "island_id": r_p_data["island_id"],
            "country_id": r_p_data["country_id"],
            "visitor_member_savedata_id": p_member_id,
            "friend_type": friend_type,
            "updated_at": current_time,
            "pokemon_nickname": pkmn["pokemon_nickname"],
            "pokemon_name": text.lookup_str("pokemon", pkmn["pokemon_no"]),
            "pokemon_no": pkmn["pokemon_no"],
            "form_no": pkmn.get("form_no", 0),
            "oyaname": pkmn["oyaname"],
            "level": pkmn["level"],
            "sex_id": pkmn["sex"],
            "personality": text.lookup_str("nature", pkmn["personality"]),
            "type1": text.lookup_str("type", pkmn["type1"]),
            "type2": text.lookup_str("type", pkmn["type2"]),
            "is_pdw": is_pdw,
            "is_gts": 0,
            "is_ds": 0,
            "exchange_flag": 0,
            "water_flag": 0
        }
        print_list["list"].append(footprint)
        db.f_write(member_id, "footprint_list", print_list)

def watered_footprint_plot(member_id: int):
    p_data = db.read(save_data.gscd, "player_data")
    r_p_data = p_data["member"]
    p_member_id = r_p_data["member_id"]
    f_p_data = db.f_read(member_id, "friend_data")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    pkmn = db.read(save_data.gscd, "sleeping_pokemon")
    player_spot = fetch_player_by_id(member_id, p_member_id)
    print_list = db.f_read(member_id, "footprint_list")
    index_print = fetch_player_footprint_plot(member_id, p_member_id)
    player_print_fetch = print_list["list"].index(index_print)
    player_print = print_list["list"][player_print_fetch]

    if player_print["water_flag"] == 0: 
        print_list["list"][player_print_fetch] = {
            "pgl_name": player_print["pgl_name"],
            "island_id": player_print["island_id"],
            "country_id": player_print["country_id"],
            "visitor_member_savedata_id": p_member_id,
            "friend_type": player_print["friend_type"],
            "updated_at": current_time,
            "pokemon_nickname": player_print["pokemon_nickname"],
            "pokemon_name": player_print["pokemon_name"],
            "pokemon_no": player_print["pokemon_no"],
            "form_no": player_print["form_no"],
            "oyaname": player_print["oyaname"],
            "level": player_print["level"],
            "sex_id": player_print["sex_id"],
            "personality": player_print["personality"],
            "type1": player_print["type1"],
            "type2": player_print["type2"],
            "is_pdw": player_print["is_pdw"],
            "is_gts": player_print["is_gts"],
            "is_ds": player_print["is_ds"],
            "exchange_flag": player_print["exchange_flag"],
            "water_flag": 1
        }

        redundant_fields = {"kinomi", "kinomi_id"}
        print_data = {
            "list": [
                {k: v for k, v in item.items() if k not in redundant_fields}
                for item in print_list["list"]
            ]
        }

        db.f_write(member_id, "footprint_list", print_data)
        print("Someone just watered someone else's plants!")
    else:
        return

def swapped_footprint_plot(member_id: int):
    p_data = db.read(save_data.gscd, "player_data")
    r_p_data = p_data["member"]
    p_member_id = r_p_data["member_id"]
    f_p_data = db.f_read(member_id, "friend_data")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    pkmn = db.read(save_data.gscd, "sleeping_pokemon")
    player_spot = fetch_player_by_id(member_id, p_member_id)
    print_list = db.f_read(member_id, "footprint_list")
    index_print = fetch_player_footprint_plot(member_id, p_member_id)
    player_print_fetch = print_list["list"].index(index_print)
    player_print = print_list["list"][player_print_fetch]

    if player_print["exchange_flag"] == 0: 
        print_list["list"][player_print_fetch] = {
            "pgl_name": player_print["pgl_name"],
            "island_id": player_print["island_id"],
            "country_id": player_print["country_id"],
            "visitor_member_savedata_id": p_member_id,
            "friend_type": player_print["friend_type"],
            "updated_at": current_time,
            "pokemon_nickname": player_print["pokemon_nickname"],
            "pokemon_name": player_print["pokemon_name"],
            "pokemon_no": player_print["pokemon_no"],
            "form_no": player_print["form_no"],
            "oyaname": player_print["oyaname"],
            "level": player_print["level"],
            "sex_id": player_print["sex_id"],
            "personality": player_print["personality"],
            "type1": player_print["type1"],
            "type2": player_print["type2"],
            "is_pdw": player_print["is_pdw"],
            "is_gts": player_print["is_gts"],
            "is_ds": player_print["is_ds"],
            "exchange_flag": 1,
            "water_flag": player_print["water_flag"]
        }

        redundant_fields = {"kinomi", "kinomi_id"}
        print_data = {
            "list": [
                {k: v for k, v in item.items() if k not in redundant_fields}
                for item in print_list["list"]
            ]
        }

        db.f_write(member_id, "footprint_list", print_data)
        print("Swap Time!")
    else:
        return

def friend_footprint_plot(member_id: int):
    p_data = db.read(save_data.gscd, "player_data")
    r_p_data = p_data["member"]
    p_member_id = r_p_data["member_id"]
    f_p_data = db.f_read(member_id, "friend_data")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    pkmn = db.read(save_data.gscd, "sleeping_pokemon")
    player_spot = fetch_player_by_id(member_id, p_member_id)
    
    if player_spot is not None:
        player = f_p_data["friend_list"].index(player_spot)
        p_fs = f_p_data["friend_list"][player]["friend_status"]

        if p_fs > 1:
            if p_fs == 3:
                friend_type = 2
                is_pdw = 1

                p_print_list = db.read(save_data.gscd, "footprint_list")
                p_index_print = fetch_friend_footprint_plot(member_id)
                friend_print_fetch = p_print_list["list"].index(p_index_print)
                friend_print = p_print_list["list"][friend_print_fetch]
                p_print_list["list"][friend_print_fetch] = {
                    "pgl_name": friend_print["pgl_name"],
                    "island_id": friend_print["island_id"],
                    "country_id": friend_print["country_id"],
                    "visitor_member_savedata_id": member_id,
                    "friend_type": friend_type,
                    "updated_at": current_time,
                    "pokemon_nickname": friend_print["pokemon_nickname"],
                    "pokemon_name": friend_print["pokemon_name"],
                    "pokemon_no": friend_print["pokemon_no"],
                    "form_no": friend_print["form_no"],
                    "oyaname": friend_print["oyaname"],
                    "level": friend_print["level"],
                    "sex_id": friend_print["sex_id"],
                    "personality": friend_print["personality"],
                    "type1": friend_print["type1"],
                    "type2": friend_print["type2"],
                    "is_pdw": is_pdw,
                    "is_gts": friend_print["is_gts"],
                    "is_ds": friend_print["is_ds"],
                    "exchange_flag": friend_print["exchange_flag"],
                    "water_flag": friend_print["water_flag"]
                }
                redundant_fields = {"kinomi", "kinomi_id"}
                print_data = {
                    "list": [
                        {k: v for k, v in item.items() if k not in redundant_fields}
                        for item in p_print_list["list"]
                    ]
                }

                db.write(save_data.gscd, "footprint_list", print_data)

            else:
                friend_type = 1
                is_pdw = 0
        else:
            friend_type = 0
            is_pdw = 0 
    else:
        friend_type = 0
        is_pdw = 0

    print_list = db.f_read(member_id, "footprint_list")
    index_print = fetch_player_footprint_plot(member_id, p_member_id)
    player_print_fetch = print_list["list"].index(index_print)
    player_print = print_list["list"][player_print_fetch]
    print_list["list"][player_print_fetch] = {
        "pgl_name": player_print["pgl_name"],
        "island_id": player_print["island_id"],
        "country_id": player_print["country_id"],
        "visitor_member_savedata_id": p_member_id,
        "friend_type": friend_type,
        "updated_at": current_time,
        "pokemon_nickname": player_print["pokemon_nickname"],
        "pokemon_name": player_print["pokemon_name"],
        "pokemon_no": player_print["pokemon_no"],
        "form_no": player_print["form_no"],
        "oyaname": player_print["oyaname"],
        "level": player_print["level"],
        "sex_id": player_print["sex_id"],
        "personality": player_print["personality"],
        "type1": player_print["type1"],
        "type2": player_print["type2"],
        "is_pdw": is_pdw,
        "is_gts": player_print["is_gts"],
        "is_ds": player_print["is_ds"],
        "exchange_flag": player_print["exchange_flag"],
        "water_flag": player_print["water_flag"]
    }
    redundant_fields = {"kinomi", "kinomi_id"}
    print_data = {
        "list": [
            {k: v for k, v in item.items() if k not in redundant_fields}
            for item in print_list["list"]
        ]
    }

    db.f_write(member_id, "footprint_list", print_data)