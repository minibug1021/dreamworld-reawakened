"""Logging a browser session in to a Trainer Club account."""
from flask import session

from utils import save_data
from utils.account_manager import accounts
from utils.models import Account

DAILY_LOGIN_BONUS_POINTS = 50


def log_in(account: Account) -> None:
    """Log this browser session in to an activated account and give the daily login bonus."""
    session["username"] = account["username"]

    if account["active_gscd"]:
        session["gscd"] = account["active_gscd"]

    if accounts.claim_daily_bonus(account["username"], save_data.today_jst_str()) and session.get("gscd"):
        save_data.award_points(DAILY_LOGIN_BONUS_POINTS)
