"""pgl.top.*: the PGL home page's site stats, login, and the logged-in player's state."""
import time

from flask import session
from werkzeug.security import check_password_hash

from api.routes import Query, endpoint
from game_sync_server.entralinked.utility.db_manager import db
from utils import language, managers, save_data, text
from utils.account_manager import accounts
from utils.auth import log_in
from utils.constants import SECONDS_PER_DAY, SECONDS_PER_HOUR
from utils.messages import message
from utils.models import Account, Member

DAYS_UNTIL_ITEM_DELETION = 100
BERRY_DREAM_POINTS       = 10

# TEMPORARY: bypass the 1-hour PDW play limit (and the 20-hour re-entry
# cooldown). Set to False to restore the original behavior.
DISABLE_PLAY_TIME_LIMIT     = True
NO_LIMIT_HOUR_TIMER_SECONDS = 2_000_000
NO_LIMIT_REMAINTIME         = 19 * SECONDS_PER_HOUR + NO_LIMIT_HOUR_TIMER_SECONDS


@endpoint("pgl.top.index")
def index(_query: Query) -> dict:
    """Site statistics."""
    return {"stats": {"pgl_population": accounts.count_accounts()}}


def _check_item_deletion(member: Member) -> None:
    """If it's been 100+ days since the last login, convert Berries to Dream Points."""
    if member.get("item_deleted_flag"):
        return

    last_started_at = member.get("last_started_at")
    if last_started_at is None:
        return

    days_away = (time.time() - last_started_at) / SECONDS_PER_DAY
    if days_away < DAYS_UNTIL_ITEM_DELETION:
        return

    exchange_point = managers.get_chest().convert_stale_berries(BERRY_DREAM_POINTS)
    if not exchange_point:
        return

    changes: Member = {"item_deleted_flag": 1, "item_deleted_point": exchange_point}
    member.update(changes)
    save_data.update_member(changes)


@endpoint("pgl.top.init")
def init(_query: Query) -> dict:
    """Return the logged-in player's data.

    The client reads the login state from the following:

    - no "member" key: not logged in (PGL.NOT_LOGGED_IN).
    - "member" without a pgl_name: logged in, but the player hasn't submitted the register
      page yet, which links a Game Sync ID and sets the PGL nickname (PGL.NOT_SIGNED_UP).
    - "member" with trial_flag 1: registered without a Game Sync ID and uses demo (PGL.TRIAL)."""
    if "username" not in session:
        return {}

    db.expire_stale(save_data.now_jst_str())
    account = accounts.get_account_by_username(session["username"])
    if account is None:
        session.clear()  # the account is gone, so the session is logged out
        return {}

    return {**_member_data(account), "username": account["username"]}


def last_up_time_text(member: Member) -> str | None:
    """Return the last tucked-in time."""
    tucked_in_at = member.get("last_up_time_strict")  # only set at tuck-in
    if tucked_in_at:
        return language.localize_last_up_time(save_data.parse_jst_str(tucked_in_at))
    return member.get("last_up_time")


def _member_data(account: Account) -> dict:
    """The "member" part of pgl.top.init for a logged-in account."""
    if "gscd" not in session:
        if not account["registered"]:
            return {"member": {}}
        return {"member": {"pgl_name": account["username"], "trial_flag": 1, "gsid_count": 0}}

    response = save_data.read_player_data()
    member = response.get("member")

    if not member:
        return {"member": {}}

    _check_item_deletion(member)

    if member.get("pokemon_no") is not None:
        member["pokemon_name"] = text.lookup_str("pokemon", member["pokemon_no"],
                                                 language.game_language(member.get("langcode")))

    if member.get("rom_id") is not None:
        member["rom_name"] = text.lookup_str("game", member["rom_id"])

    member["last_up_time"] = last_up_time_text(member)

    # only the response is changed, the saved nextstart_remaintime is untouched
    if DISABLE_PLAY_TIME_LIMIT:
        member["nextstart_remaintime"] = NO_LIMIT_REMAINTIME
    else:
        member["nextstart_remaintime"] = save_data.get_nextstart_remaintime()

    return dict(response)


@endpoint("pgl.top.login", methods=("POST",))  # custom API call - not original
def login(query: Query) -> dict:
    """Check a username and password and log the browser session in."""
    username = query.get("username", "")
    password = query.get("password", "")

    accounts.delete_expired_accounts()
    account = accounts.get_account_by_username(username)

    if account is None or not check_password_hash(account["password_hash"], password):
        return {"error": message("bad_login")}

    if not account["activated"]:
        return {"error": message("not_activated")}

    log_in(account)
    return {}

