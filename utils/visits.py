"""Visiting other players' islands."""
from game_sync_server.entralinked.utility.db_manager import db
from utils import save_data
from utils.account_manager import accounts
from utils.models import Member

FRIEND_WATERINGS_PER_DAY = 20


def can_see(viewer: str, other: str) -> bool:
    """Return whether the player `viewer` can see and visit `other`'s island."""
    if other == viewer or not db.read(other, "sleeping_pokemon"):
        return False
    owner = accounts.get_gscd_owner(other)
    account = accounts.get_account_by_username(owner)
    if not account:
        return False
    viewer_owner = accounts.get_gscd_owner(viewer)
    if owner == viewer_owner:
        return True
    viewer_account = accounts.get_account_by_username(viewer_owner)
    # The profile setting decides who can visit, and the stricter of the two players'
    # settings applies to both.
    return account["pgl_privacy"] == "everyone" and bool(viewer_account) and viewer_account["pgl_privacy"] == "everyone"


def neighbors(gscd: str | None = None) -> list[Member]:
    """Return every player shown on the map around `gscd`'s island."""
    center = save_data.require_gscd(gscd)
    left_out = {center, save_data.get_current_gscd()}
    return [save_data.read_member(other) for other in db.get_all_gscds()
            if other not in left_out and can_see(center, other)]


def find_player(member_savedata_id: int, gscd: str | None = None) -> str:
    """Return the Game Sync ID of the player with this member_savedata_id.

    Raise ValueError if no player has it, or if it belongs to someone the player can't
    visit. The player's own id is always allowed.
    """
    me = save_data.require_gscd(gscd)
    other = db.find_gscd(member_savedata_id)
    if other is None or (other != me and not can_see(me, other)):
        raise ValueError(f"No visible player with member_savedata_id {member_savedata_id}")
    return other


def friend_waterings_left(gscd: str | None = None) -> int:
    """How many times the player can still water other players' gardens today."""
    member = save_data.read_member(gscd)
    if member.get("friend_waterings_date") != save_data.today_jst_str():
        return FRIEND_WATERINGS_PER_DAY
    return member.get("friend_waterings_left", FRIEND_WATERINGS_PER_DAY)


def use_friend_watering(gscd: str | None = None) -> int:
    """Use up one of today's waterings and return how many are left.

    Raise ValueError, and use nothing, if none are left.
    """
    today = save_data.today_jst_str()

    def use(member: Member) -> None:
        left = member.get("friend_waterings_left", FRIEND_WATERINGS_PER_DAY)
        if member.get("friend_waterings_date") != today:
            left = FRIEND_WATERINGS_PER_DAY
        if left <= 0:
            raise ValueError("No waterings left today")
        member["friend_waterings_left"] = left - 1
        member["friend_waterings_date"] = today

    return save_data.change_member(use, save_data.require_gscd(gscd))["friend_waterings_left"]
