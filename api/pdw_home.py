"""pdw.home.*: the player's house and island (pdw_home.swf, pdw_room.swf)."""
import time
from random import randint

from api.routes import Query, endpoint, query_int
from game_sync_server.entralinked.utility.db_manager import db
from utils import pokemon, save_data, text, visits
from utils.account_manager import accounts
from utils.constants import DREAMLAND_VISITS_PER_SESSION, SHARE_SHELF_ID, DreamPalStatus, PlayerStatus
from utils.decor import arranged_decor
from utils.language import game_language
from utils.models import Member, SleepingPokemon

DAILY_BONUS_POINTS = 50


def _footprint(island_gscd: str, row: dict) -> dict:
    """Return a visitor's footprint data."""
    visitor = save_data.read_member(row["visitor_gscd"])
    pkmn = pokemon.get_sleeper(row["visitor_gscd"])
    status = db.dream_pal_status(island_gscd, row["visitor_gscd"])
    return {
        "visitor_member_savedata_id": visitor.get("member_savedata_id"),
        "member_id":        visitor.get("member_id"),
        "pgl_name":         visitor.get("pgl_name"),
        "player_name":      visitor.get("player_name"),
        "island_id":        visitor.get("island_id"),
        "country_id":       visitor.get("country_id"),
        "is_pdw":           int(status == DreamPalStatus.PALS),
        "is_gts":           0,
        "is_ds":            0,
        # 1 shows the visitor's Dream Pal request, 2 that they're a Dream Pal
        "friend_type":      {DreamPalStatus.REQUESTED: 1, DreamPalStatus.PALS: 2}.get(status, 0),
        "updated_at":       row["visited_at"][:16],
        "exchange_flag":    row["swapped"],
        "water_flag":       row["watered"],
        "pokemon_no":       pkmn["pokemon_no"],
        "form_no":          pkmn.get("form_no", 0),
        "pokemon_name":     text.lookup_str("pokemon", pkmn["pokemon_no"], game_language(visitor.get("langcode"))),
        "pokemon_nickname": pkmn["pokemon_nickname"],
        "oyaname":          pkmn["oyaname"],
        "level":            pkmn["level"],
        "type1":            text.lookup_str("type", pkmn["type1"]),
        "type2":            text.lookup_str("type", pkmn["type2"]),
        "sex_id":           pkmn["sex"],
        "personality":      text.lookup_str("nature", pkmn["personality"]),
    }


@endpoint("pdw.home.footprint_list")
def footprint_list(query: Query) -> dict:
    """Return a page of the players who visited the player's island."""
    me = save_data.require_gscd()
    rows = [row for row in db.footprints(me) if visits.can_see(me, row["visitor_gscd"])]
    offset = query_int(query, "offset", 0)
    page = rows[offset:offset + query_int(query, "rowcount", 12)]
    return {"list": [_footprint(me, row) for row in page], "cnt": len(rows)}


def _island_pokemon(pkmn: SleepingPokemon, langcode: int | None) -> dict:
    """A tucked-in Pokémon."""
    return {
        **pkmn,
        "pokemon_name": text.lookup_str("pokemon", pkmn["pokemon_no"], game_language(langcode)),
        "type1":        text.lookup_str("type", pkmn["type1"]),
        "type2":        text.lookup_str("type", pkmn["type2"]),
        "personality":  text.lookup_str("nature", pkmn["personality"]),
        "ball_name":    text.lookup_str("ball", pkmn["ball_name"]),
        "shiny":        pokemon.shows_shiny(pkmn.get("is_shiny", False)),
    }


@endpoint("pdw.home.my_island")
def my_island(_query: Query) -> dict:
    """Return the player's island with their house, furniture, and the tucked-in Pokémon."""
    member = save_data.read_member()
    return {
        "pokemon":                _island_pokemon(pokemon.get_sleeper(), member.get("langcode")),
        "island_id":              member["island_id"],
        "point":                  0,
        "trial_flag":             0,
        "arranged_interior_list": arranged_decor(),
        "requested_flag":         False,
        "shelf_id":               member["shelf_id"],
        "item_deleted_flag":      member.get("item_deleted_flag", 0),
    }


def _island_area(gscd: str) -> dict:
    """Return the map around a player's island: their island and the players they can visit."""
    pals = {save_data.read_member(pal)["member_savedata_id"] for pal in db.dream_pals(gscd, DreamPalStatus.PALS)}
    friends = [
        {
            "pgl_name":           member.get("pgl_name"),
            "member_id":          member.get("member_id"),
            "member_savedata_id": member.get("member_savedata_id"),
            "island_id":          member.get("island_id"),
            "country_id":         member.get("country_id"),
            "is_ds":              0,
            "is_gts":             0,
            "is_pdw":             int(member.get("member_savedata_id") in pals),  # the Dream Pal bridge
        }
        for member in visits.neighbors(gscd)
    ]
    return {"island_id": save_data.read_member(gscd)["island_id"], "friend_list": friends}


@endpoint("pdw.home.my_island_area")
def my_island_area(_query: Query) -> dict:
    """Return the map around the player's own island."""
    return _island_area(save_data.require_gscd())


@endpoint("pdw.home.friend_island_area")
def friend_island_area(query: Query) -> dict:
    """Return the map around another player's island, which the player is visiting."""
    return _island_area(visits.find_player(int(query["friend_member_savedata_id"])))


@endpoint("pdw.home.friend_island")
def friend_island(query: Query) -> dict:
    """Return another player's island."""
    me = save_data.require_gscd()
    friend = visits.find_player(int(query["friend_member_savedata_id"]))
    member = save_data.read_member(friend)
    if friend != me:
        db.record_footprint(friend, me, save_data.now_jst_str())
    return {
        "pokemon":                _island_pokemon(pokemon.get_sleeper(), save_data.read_member(me).get("langcode")),
        "friend_pokemon":         _island_pokemon(pokemon.get_sleeper(friend), member.get("langcode")),
        "friend_status":          db.dream_pal_status(me, friend),
        "visit_count":            db.record_dream_pal_visit(me, friend, save_data.today_jst_str()),
        "island_id":              member["island_id"],
        "point":                  0,
        "trial_flag":             0,
        "arranged_interior_list": arranged_decor(friend),
        "requested_flag":         False,
        "shelf_id":               SHARE_SHELF_ID,
    }


def _send_request(other_id: str) -> bool:
    """Send a Dream Pal request and return whether the two players are now Dream Pals."""
    me = save_data.require_gscd()
    other = visits.find_player(int(other_id))
    return db.request_dream_pal(me, other, save_data.now_jst_str())


@endpoint("pdw.home.friend_request", methods=("POST",))
def friend_request(query: Query) -> dict:
    """Send a Dream Pal request to another player."""
    return {"joined": int(_send_request(query["friend_member_savedata_id"]))}


@endpoint("pdw.home.friend_accept", methods=("POST",))
def friend_accept(query: Query) -> dict:
    """Accept a Dream Pal request from another player."""
    _send_request(query["visitor_member_savedata_id"])
    return {}


@endpoint("pdw.home.pdw_end")
def pdw_end(_query: Query) -> dict:
    """End the Dream World session so the Pokémon can be woken."""
    save_data.set_play_status(PlayerStatus.WAKE_READY)
    return {}


@endpoint("pdw.home.pdw_start", methods=("POST",))
def pdw_start(_query: Query) -> dict:
    """Start a Dream World session.

    The first session of the day (JST) for each account also gives the daily bonus.
    """
    timestamp = int(time.time())
    gscd = save_data.require_gscd()
    if not save_data.is_dreaming(gscd):
        raise ValueError("No Pokémon is dreaming")
    member = save_data.read_member(gscd)

    db.expire_stale(save_data.now_jst_str())
    save_data.record_session_start(timestamp)
    pokemon_name = text.lookup_str("pokemon", member["pokemon_no"], game_language(member.get("langcode")))
    update: Member = {"pokemon_name": pokemon_name, "point": 0,
                      "dreamland_visits_left": randint(*DREAMLAND_VISITS_PER_SESSION)}
    if member.get("first_flag") == 0:
        update["first_flag"] = 1
    save_data.update_member(update)

    # after the reset above, so the bonus counts toward this session's points
    owner = accounts.get_gscd_owner(gscd)
    if owner and accounts.claim_daily_bonus(owner, save_data.today_jst_str()):
        save_data.award_points(DAILY_BONUS_POINTS, gscd)

    return {"started_at": timestamp}


@endpoint("pdw.home.pdw_timecheck", methods=("POST",))
def pdw_timecheck(_query: Query) -> dict:
    """Save how long is left before the next session can start."""
    save_data.update_member({"nextstart_remaintime": save_data.get_nextstart_remaintime()})
    return {}


@endpoint("pdw.home.item_deleted_check", methods=("POST",))
def item_deleted_check(_query: Query) -> dict:
    """Shown once after Berries are converted to Dream Points (see pgl_top._check_item_deletion)."""
    exchange_point = save_data.read_member().get("item_deleted_point", 0)
    save_data.update_member({"item_deleted_flag": 0, "item_deleted_point": 0})
    return {"exchange_point": exchange_point}
