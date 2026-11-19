"""Per-player saved data.

This relates to the player_data and game_sync columns of game_sync_server's player_saves table.

Every function takes an optional `gscd`. Without one it uses the Game Sync ID of the
logged-in browser session. Reads of a missing save return empty dicts. Writes without a
Game Sync ID do nothing. Member changes go through db.update.

The game-sync server imports this module as well.
"""
import time
from collections.abc import Callable
from datetime import datetime
from random import randint
from typing import cast
from zoneinfo import ZoneInfo

from flask import session

from game_sync_server.entralinked.utility.db_manager import db
from utils import text
from utils.constants import SECONDS_PER_HOUR, PlayerStatus
from utils.models import EntralinkItem, GameSync, Member, PlayerData

JST = ZoneInfo("Asia/Tokyo")

DREAM_WORLD_TOTAL_COOLDOWN_SECONDS = 20 * SECONDS_PER_HOUR


def now_jst_str() -> str:
    """Return the current server time formatted like the JST-family member fields.

    Those are member_created_at, last_up_time_strict, pdw_copied_at, pgl_copied_at, and
    deleted_at.
    """
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")


def parse_jst_str(value: str) -> int:
    """Return the epoch timestamp of a time formatted by now_jst_str."""
    return int(datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=JST).timestamp())


def today_jst_str() -> str:
    """Return the current server date (JST), used to gate the once-per-day login bonus."""
    return datetime.now(JST).strftime("%Y-%m-%d")


def get_current_gscd() -> str | None:
    """Return the gscd linked to the logged-in account on this browser session.

    Return None if nobody's logged in / linked a Game Sync ID yet.
    """
    return session.get("gscd")


def resolve_gscd(gscd: str | None = None) -> str | None:
    """`gscd` if given, else the logged-in session's Game Sync ID (which may be None)."""
    return gscd or get_current_gscd()


def require_gscd(gscd: str | None = None) -> str:
    """Like resolve_gscd, but raises ValueError when there's no Game Sync ID at all."""
    gscd = resolve_gscd(gscd)
    if not gscd:
        raise ValueError("No active Game Sync ID - the player must be logged in and synced.")
    return gscd


def generate_otoken(world_id: int) -> str:
    """Return a one-off token for a dreamland object."""
    return f"{randint(1, 99)}dwt{world_id}{int(time.time()):x}.{randint(10000000, 99999999)}"


# ---------------
# player data
# ---------------

def read_player_data(gscd: str | None = None) -> PlayerData:
    """Return the whole player_data column ({} without a save)."""
    gscd = resolve_gscd(gscd)
    if not gscd:
        return {}
    return cast(PlayerData, db.read(gscd, "player_data") or {})


def read_medals(gscd: str | None = None) -> list[dict]:
    """Return the player's Medals, newest first.

    Each one is {"medal_id", "medal_name", "is_recommend"}.
    """
    player_data = read_player_data(gscd)
    favorite = player_data.get("favorite_medal")
    return [{"medal_id": medal_id,
             "medal_name": text.lookup_str("medal", medal_id),
             "is_recommend": medal_id == favorite}
            for medal_id in player_data.get("medals", [])]


def read_member(gscd: str | None = None) -> Member:
    """Return the player's PGL profile ({} without a save)."""
    return read_player_data(gscd).get("member", {})


def change_member(change: Callable[[Member], None], gscd: str | None = None) -> Member:
    """Atomically apply `change` (which edits the member in place) and save it.

    Return the updated member ({} without a Game Sync ID).
    """
    gscd = resolve_gscd(gscd)
    if not gscd:
        return {}

    def change_player_data(player_data: dict) -> None:
        change(player_data.setdefault("member", {}))

    return cast(PlayerData, db.update(gscd, "player_data", change_player_data))["member"]


def update_member(changes: Member, gscd: str | None = None) -> Member:
    """Merge `changes` into the saved member and return the updated member."""
    return change_member(lambda member: member.update(changes), gscd)


def award_points(amount: int, gscd: str | None = None) -> None:
    """Add Dream Points."""
    def add(member: Member) -> None:
        member["point"] = (member.get("point") or 0) + amount
        member["experiment_point"] = (member.get("experiment_point") or 0) + amount

    change_member(add, gscd)


def use_dreamland_visit(gscd: str | None = None) -> bool:
    """Use up a Dream Island visit if the session has one, and return whether it did."""
    used = False

    def use(member: Member) -> None:
        nonlocal used
        if member.get("dreamland_visits_left", 0) > 0:
            member["dreamland_visits_left"] -= 1
            used = True

    change_member(use, gscd)
    return used


def record_session_start(timestamp: int, gscd: str | None = None) -> None:
    """Record that a Dream World session started.

    last_logined_at is always the same instant as last_started_at.
    last_started_at_timezone is the same instant for the local clock.
    """
    update_member({"last_started_at": timestamp, "last_logined_at": timestamp,
                   "last_started_at_timezone": timestamp}, gscd)


def get_nextstart_remaintime(gscd: str | None = None) -> int:
    """Return the seconds left before the next Dream World session can start."""
    last_started_at = read_member(gscd).get("last_started_at")
    if last_started_at is None:
        return 0
    next_start_at = last_started_at + DREAM_WORLD_TOTAL_COOLDOWN_SECONDS
    return max(0, next_start_at - int(time.time()))


def set_play_status(status: PlayerStatus) -> None:
    """Change the state of a tucked-in Pokémon."""
    gscd = get_current_gscd()
    if not gscd or not db.read(gscd, "game_sync"):
        raise ValueError("A sleeping Pokémon must be tucked to bed first.")
    update_member({"play_status": status.value})


# ---------------
# game sync data
# ---------------

def read_game_sync() -> GameSync:
    """Return the logged-in player's game_sync column ({} without a save)."""
    gscd = get_current_gscd()
    if not gscd:
        return {}
    return cast(GameSync, db.read(gscd, "game_sync") or {})


def change_game_sync(change: Callable[[GameSync], None]) -> None:
    """Atomically applies `change` (which edits the game_sync data in place) and saves it."""
    gscd = get_current_gscd()
    if gscd:
        db.update(gscd, "game_sync", cast(Callable[[dict], None], change))


def write_entralink_items(items: list[EntralinkItem]) -> None:
    """Save the items queued to go to the DS at the next Game Sync."""
    def set_items(game_sync: GameSync) -> None:
        game_sync["items"] = items

    change_game_sync(set_items)
