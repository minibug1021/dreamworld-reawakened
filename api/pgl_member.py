import json

from utils import text
from utils import pokemon
from utils import save_data
from game_sync_server.entralinked.utility.db_manager import db

# ---------------------
# GET API calls
# ---------------------

def GET_profile_customize(_query):
    response = {
    "selected": {
        "cgear":   "01",
        "pokedex": "01",
        "musical": "01"
    },
    "cgear":   ["01", "02", "03"],
    "pokedex": ["01", "02"],
    "musical": ["01", "02", "03"]
    }

    return json.dumps(response).encode()


def GET_profile_friend_friend_list(_query):
    return b"{}"


def GET_profile_friend_gbu_profile(_query):
    return b"{}"


def GET_profile_friend_list(_query):
    m = save_data.read_player_data()["member"]
    friend_template = {
        "avator_id":          m["avator_id"],
        "pgl_name":           m["pgl_name"],
        "member_savedata_id": str(m["member_savedata_id"]),
        "disable_flag":       str(m["disable_flag"] or 0),
        "is_ds":              True,
        "country_code":       "US",
        "is_blocked":         "0",
    }
    response = {
        "list": [friend_template],
        "cnt":  1,
    }
    return json.dumps(response).encode()


def GET_profile_friend_pdw_friend_list(_query):
    return b"{}"


def GET_profile_friend_pdw_profile_by_pgl(_query):
    return b"{}"


def GET_profile_friend_profile(_query):
    return b"{}"


def GET_profile_gsid_list(_query):
    return b"{}"


def GET_profile_my_gbu_profile(_query):
    return b"{}"


def GET_profile_my_pdw_profile_by_pgl(_query):
    m  = save_data.read_player_data()["member"]
    sp = pokemon.sleeper
    response = {
        "island_id":        m["island_id"],
        "experiment_point": m["experiment_point"],
        "pokemon_name":     text.lookup_str("pokemon", m["pokemon_no"]),
        "pokemon_nickname": sp["pokemon_nickname"],
        "level":            sp["level"],
        "sex_id":           sp["sex"],
        "pokemon_no":       m["pokemon_no"],
        "form_no":          m["form_no"],
        "oyaname":          sp["oyaname"],
        "type1":            text.lookup_str("type", m["type1"]),
        "type2":            text.lookup_str("type", m["type2"]),
        "personality":      text.lookup_str("nature", sp["personality"]),
        "encount_pokemons": [],
    }
    return json.dumps(response).encode()


def GET_profile_my_profile(_query):
    p = save_data.read_player_data()
    m = p["member"]
    g = save_data.read_entralink_data()

    playtime_str = f"{g['hours_played']:02}:{g['minutes_played']:02}"

    response = {
        "avator_id":           m["avator_id"],
        "pgl_name":            m["pgl_name"],
        "country_name":        text.lookup_str("country", m["country_id"]),
        "rom_name":            text.lookup_str("game", m["rom_id"]),
        "rom_id":              str(m["rom_id"]),
        "trial_flag":          str(m["trial_flag"]),
        "player_badge_num":    m["player_badge_num"],
        "langcode":            m["langcode"],
        "trainer_name":        m["player_name"],
        "playtime":            playtime_str,
        "disclosure_flag":     m["disclosure_flag"],
        "list_disclosure_flag": m["list_disclosure_flag"],
        "friends":             [],
        "friends_count":       0,
        "medals":              p.get("medals", []),
    }

    return json.dumps(response).encode()


def GET_profile_my_state(_query):
    save_data.update_gamesync_status(save_data.PlayerStatus.DREAMING)

    return b"{}"


def GET_profile_pdw_friend_list(_query):
    return b"{}"


def GET_profile_pdw_end_by_pgl(_query):
    save_data.update_gamesync_status(save_data.PlayerStatus.WAKE_READY)
    return b"{}"


def GET_profile_video_delete(_query):
    return b"{}"


def GET_profile_video_regist(_query):
    return b"{}"

# ---------------------
# POST API calls
# ---------------------

def POST_profile_avator_list(_query):
    valid_pfps = (
        list(range(2, 5))
        + list(range(30, 34))
        + [35]
        + [37]
        + [78]
        + list(range(149, 159))
        + list(range(184, 201)) # 200 is the cutoff for PFPs available to new accounts
        + list(range(651, 856))
        + list(range(859, 868))
        + list(range(901, 908))
        + list(range(911, 916))
        + [920]
        + [1025]
    )

    response = [
        {
            "avator_id": profile_id,
            "avator_name": "Placeholder"
        }
        for profile_id in valid_pfps
    ]

    return json.dumps({"avator_list": response}).encode()


def POST_profile_avator_select(_query):
    selected_pfp = _query["avator_id"]

    save_data.write_player_data({"avator_id": selected_pfp})


def POST_profile_disclosure_switch(_query):
    flag = int(_query.get("disclosure_flag", 0))
    save_data.write_player_data({"disclosure_flag": flag})
    return b"{}"


def POST_profile_list_disclosure_switch(_query):
    flag = int(_query.get("list_disclosure_flag", 0))
    save_data.write_player_data({"list_disclosure_flag": flag})
    return b"{}"


def POST_profile_pdw_login(_query):
    return b"{}"