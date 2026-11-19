"""Logging a browser session in to a Trainer Club account."""
from flask import session

from utils.models import Account


def log_in(account: Account) -> None:
    """Log this browser session in to an activated account."""
    session["username"] = account["username"]

    if account["active_gscd"]:
        session["gscd"] = account["active_gscd"]
