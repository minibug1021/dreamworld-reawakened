"""pgl.member.profile.*: avatar, privacy settings, Game Sync ID linking, and profile pages."""
from itertools import chain

from flask import session

from api.pgl_top import last_up_time_text
from api.routes import Query, endpoint, query_int
from game_sync_server.entralinked.utility.db_manager import db
from utils import pokemon, save_data, text
from utils.account_manager import accounts
from utils.constants import PlayerStatus
from utils.language import game_language
from utils.messages import message
from utils.models import Member

GSCD_LENGTH = 10
MAX_LINKED_GSCDS = 4  # one for each of Black, White, Black 2 and White 2
DEMO_AVATAR_ID = 4

# The avatar picker offers these avator_id values. New accounts could pick ids up to 200.
AVATAR_IDS = tuple(chain(
    range(2, 5), range(30, 34), [35, 37, 78], range(149, 159), range(184, 201),
    range(651, 856), range(859, 868), range(901, 908), range(911, 916), [920, 1025],
))


def _field_error(field: str, message_id: str, **values: object) -> dict:
    """Return the response that makes the form show a message next to `field`."""
    return {"error": {"details": {field: message(message_id, **values)}}}


@endpoint("pgl.member.profile.friend_list")
def friend_list(_query: Query) -> dict:
    """Return a placeholder friend list with the player as their own only friend."""
    member = save_data.read_member()
    return {
        "list": [{
            "avator_id":          member["avator_id"],
            "pgl_name":           member["pgl_name"],
            "member_savedata_id": str(member["member_savedata_id"]),
            "disable_flag":       str(member["disable_flag"] or 0),
            "is_ds":              True,
            "country_code":       "US",
            "is_blocked":         "0",
        }],
        "cnt": 1,
    }


@endpoint("pgl.member.profile.init_create_confirm")
def init_create_confirm(query: Query) -> dict:
    """Validate the sign-up form before init_create."""
    gscd = query.get("gscd", "").strip()

    if gscd and len(gscd) != GSCD_LENGTH:
        return _field_error("gscd", "bad_gscd_length", length=GSCD_LENGTH)

    return {}


@endpoint("pgl.member.profile.my_pdw_profile_by_pgl")
def my_pdw_profile(_query: Query) -> dict:
    """Return the player's Dream World profile with their island and tucked-in Pokémon.

    A demo player uses Fennel's Munna.
    """
    if not session.get("gscd"):
        return {}
    member = save_data.read_member()
    sleeper = pokemon.get_sleeper()
    profile = {
        "island_id":        member["island_id"],
        "experiment_point": member["experiment_point"],
        "encount_pokemons": []
    }
    if not save_data.is_dreaming():
        return {**profile, **dict.fromkeys(("pokemon_name", "pokemon_nickname", "level", "sex_id", "pokemon_no",
                                            "form_no", "oyaname", "type1", "type2", "personality", "shiny"))}
    return {
        **profile,
        "pokemon_name":     text.lookup_str("pokemon", member["pokemon_no"], game_language(member.get("langcode"))),
        "pokemon_nickname": sleeper.get("pokemon_nickname"),
        "level":            sleeper.get("level"),
        "sex_id":           sleeper.get("sex"),
        "pokemon_no":       member["pokemon_no"],
        "form_no":          member["form_no"],
        "oyaname":          sleeper.get("oyaname"),
        "type1":            text.lookup_str("type", member["type1"]),
        "type2":            text.lookup_str("type", member["type2"]),
        "personality":      text.lookup_str("nature", sleeper.get("personality")),
        "shiny":            pokemon.shows_shiny(sleeper.get("is_shiny", False))
    }


def _demo_profile() -> dict:
    """The profile of a demo player, who has an account but no Game Sync ID."""
    account = accounts.get_account_by_username(session.get("username"))
    return {
        "avator_id":            DEMO_AVATAR_ID,
        "pgl_name":             account["username"] if account else "",
        "country_name":         text.lookup_str("country", account["country"] if account else None),
        "rom_name":             "",
        "rom_id":               "",
        "trial_flag":           "1",
        "player_badge_num":     0,
        "langcode":             None,
        "trainer_name":         "",
        "playtime":             "",
        "disclosure_flag":      0,
        "list_disclosure_flag": 0,
        "friends":              [],
        "friends_count":        0,
        "medals":               [],
    }


@endpoint("pgl.member.profile.my_profile")
def my_profile(_query: Query) -> dict:
    """Return the player's PGL profile page."""
    if not session.get("gscd"):
        return _demo_profile()
    player_data = save_data.read_player_data()
    member = player_data["member"]
    game_sync = save_data.read_game_sync()
    country_id = accounts.get_country_id(session.get("username"))

    return {
        "avator_id":            member["avator_id"],
        "pgl_name":             member["pgl_name"],
        "country_name":         text.lookup_str("country", country_id),
        "rom_name":             text.lookup_str("game", member["rom_id"]),
        "rom_id":               str(member["rom_id"]),
        "trial_flag":           str(member["trial_flag"]),
        "player_badge_num":     member["player_badge_num"],
        "langcode":             member["langcode"],
        "trainer_name":         member["player_name"],
        "playtime":             f"{game_sync['hours_played']:02}:{game_sync['minutes_played']:02}",
        "disclosure_flag":      member["disclosure_flag"],
        "list_disclosure_flag": member["list_disclosure_flag"],
        "friends":              [],
        "friends_count":        0,
        "medals":               save_data.read_medals(),
    }


@endpoint("pgl.member.profile.my_state")
def my_state(_query: Query) -> dict:
    """Make the tucked-in Pokémon start dreaming."""
    save_data.set_play_status(PlayerStatus.DREAMING)
    return {}


@endpoint("pgl.member.profile.pdw_end_by_pgl")
def pdw_end_by_pgl(_query: Query) -> dict:
    """End the Dream World session so the Pokémon can be woken up."""
    save_data.set_play_status(PlayerStatus.WAKE_READY)
    return {}


@endpoint("pgl.member.profile.rom_check")
def rom_check(query: Query) -> dict:
    """Which game a Game Sync ID belongs to."""
    gscd = query.get("gscd", "").strip()
    if gscd and not db.gscd_exists(gscd):
        return _field_error("gscd", "gscd_not_found")
    return {"rom_id": save_data.read_member(gscd).get("rom_id") if gscd else None}


@endpoint("pgl.member.profile.avator_list", methods=("POST",))
def avatar_list(_query: Query) -> dict:
    """Return the avatars the picker offers."""
    return {"avator_list": [{"avator_id": avatar_id, "avator_name": text.lookup_str("avatar", avatar_id)}
                            for avatar_id in AVATAR_IDS]}


@endpoint("pgl.member.profile.avator_select", methods=("POST",))
def avatar_select(query: Query) -> dict:
    """Change the player's avatar."""
    save_data.update_member({"avator_id": int(query["avator_id"])})
    return {}


@endpoint("pgl.member.profile.disclosure_switch", methods=("POST",))
def disclosure_switch(query: Query) -> dict:
    """Save the disclosure_flag privacy setting."""
    save_data.update_member({"disclosure_flag": query_int(query, "disclosure_flag", 0)})
    return {}


@endpoint("pgl.member.profile.list_disclosure_switch", methods=("POST",))
def list_disclosure_switch(query: Query) -> dict:
    """Save the list_disclosure_flag privacy setting."""
    save_data.update_member({"list_disclosure_flag": query_int(query, "list_disclosure_flag", 0)})
    return {}


def _link_gscd(username: str, gscd: str) -> dict | None:
    """Link a Game Sync ID to the account.

    Return a field error, and link nothing, if the Game Sync ID doesn't exist or is
    already linked to any account, this one included. Return None once it's linked.
    """
    if not db.gscd_exists(gscd):
        return _field_error("gscd", "gscd_not_found")

    owner = accounts.get_gscd_owner(gscd)
    if owner == username:
        return _field_error("gscd", "gscd_already_yours")
    if owner is not None:
        return _field_error("gscd", "gscd_already_taken")

    # the profile page shows one Game Sync ID per game
    linked = accounts.get_gscds_for_account(username)
    rom_id = save_data.read_member(gscd).get("rom_id")
    if len(linked) >= MAX_LINKED_GSCDS or any(save_data.read_member(other).get("rom_id") == rom_id for other in linked):
        return _field_error("gscd", "gscd_game_already_linked")

    accounts.link_gscd(username, gscd)
    session.setdefault("gscd", gscd)

    linked_gscds = accounts.get_gscds_for_account(username)
    for linked_gscd in linked_gscds:
        save_data.update_member({"gsid_count": len(linked_gscds)}, linked_gscd)
    return None


@endpoint("pgl.member.profile.init_create", methods=("POST",))
def init_create(query: Query) -> dict:
    """Finish sign-up by linking a Game Sync ID (if given) and setting the PGL nickname."""
    gscd = query.get("gscd", "").strip()
    username = session.get("username")
    if not username:
        return {"flg": 0}

    if gscd:
        error = _link_gscd(username, gscd)
        if error:
            return error

    if session.get("gscd"):
        _set_up_member(username, session["gscd"])
    accounts.mark_registered(username)

    return {"flg": 2 if session.get("gscd") else 0}


def _set_up_member(username: str, gscd: str) -> None:
    """Give a newly linked Game Sync ID's save the account's PGL nickname and country."""
    changes: Member = {"pgl_name": username, "trial_flag": 0}
    country_id = accounts.get_country_id(username)
    if country_id is not None:
        changes["country_id"] = country_id
    save_data.update_member(changes, gscd)


@endpoint("pgl.member.profile.gsid_create", methods=("POST",))
def gsid_create(query: Query) -> dict:
    """Link another Game Sync ID to the account, from the profile page.

    A trial player becomes a full member.
    """
    username = session.get("username")
    if not username:
        return _field_error("gscd", "gscd_not_found")
    gscd = query.get("gscd", "").strip()
    error = _link_gscd(username, gscd)
    if error:
        return error
    _set_up_member(username, gscd)
    return {}


@endpoint("pgl.member.profile.gsid_list")
def gsid_list(_query: Query) -> dict:
    """List the account's Game Sync IDs."""
    username = session.get("username")
    if not username:
        return {"gsid_list": []}
    gsid_list = []
    for gscd in accounts.get_gscds_for_account(username):
        member = save_data.read_member(gscd)
        gsid_list.append({
            "gscd": gscd,
            "rom_id": member.get("rom_id"),
            "rom_name": text.lookup_str("game", member.get("rom_id")),
            "last_up_time": last_up_time_text(member),
        })
    return {"gsid_list": gsid_list}


@endpoint("pgl.member.profile.gsid_switch", methods=("POST",))
def gsid_switch(query: Query) -> dict:
    """Switch an account's active Game Sync ID."""
    username = session.get("username")
    gscd = query.get("gscd", "").strip()
    if not username or not accounts.set_active_gscd(username, gscd):
        return _field_error("gscd", "gscd_not_found")
    session["gscd"] = gscd
    return {}
