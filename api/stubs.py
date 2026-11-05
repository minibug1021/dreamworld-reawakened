"""Endpoints the client calls that aren't implemented yet, which all answer with {}.

Placeholders that return made-up data live with the real endpoints of their module, and
their docstrings say they return a placeholder.
"""
from api.routes import Query, endpoint

EMPTY_STUBS = {
    "GET": (
        "hb",  # heartbeat
        "gbu.journal.season_list",
        "gbu.worldbattle.get_battle_history",
        "gts.profile.gts_history",
        "pdw.croft.tutorial_start",
        "pdw.croft.tutorial_end",
        "pdw.home.board_pokemon_list",
        "pdw.home.my_bridge",
        "pgl.member.profile.friend_friend_list",
        "pgl.member.profile.friend_gbu_profile",
        "pgl.member.profile.friend_pdw_friend_list",
        "pgl.member.profile.friend_pdw_profile_by_pgl",
        "pgl.member.profile.friend_profile",
        "pgl.member.profile.gsid_list",
        "pgl.member.profile.my_gbu_profile",
        "pgl.member.profile.pdw_friend_list",
        "pgl.member.profile.video_delete",
        "pgl.member.profile.video_regist",
        "pgl.news.news_list",
    ),
    "POST": (
        "pgl.member.profile.pdw_login",
    ),
}


def empty_response(_query: Query) -> dict:
    """Return an empty response. Every name in EMPTY_STUBS shares this handler."""
    return {}


for _method, _names in EMPTY_STUBS.items():
    for _name in _names:
        endpoint(_name, methods=(_method,))(empty_response)
