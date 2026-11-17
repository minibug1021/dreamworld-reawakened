"""Trainer Club sign-up and account activation."""
import re
import secrets
import smtplib
from typing import cast, get_args

from flask import Blueprint, Response, current_app, redirect, request
from werkzeug.security import generate_password_hash
from werkzeug.wrappers import Response as WerkzeugResponse

from config import LANG, EmailNotConfiguredError
from utils import text
from utils.account_manager import accounts
from utils.assets import ASSETS_DIR, not_found, serve_file
from utils.badwords import contains_bad_word
from utils.email_sender import send_activation_email
from utils.models import Privacy

SIGNUP_URL     = f"/www.pokemon.com/{LANG}/account/pgl/signup/"
SIGNUP_DIR     = ASSETS_DIR / "www.pokemon.com" / LANG / "account" / "pgl" / "signup"
ACTIVATION_URL = f"/www.pokemon.com/{LANG}/account/pgl/activated/<token>"

SIGNUP_FORM_FIELDS = (
    "country", "birth_month", "username", "password",
    "password_confirm", "email", "pgl_privacy", "dw_privacy",
)
PASSWORD_MIN_LENGTH = 6
USERNAME_PATTERN = re.compile(r"[A-Za-z0-9]{4,15}")
EMAIL_PATTERN = re.compile(r"[^@\s]{1,64}@[^@\s]+\.[^@\s]+")
EMAIL_MAX_LENGTH = 254
BIRTH_MONTHS = {str(month) for month in range(1, 13)}
PRIVACY_SETTINGS = set(get_args(Privacy))

signup = Blueprint("signup", __name__)


def _is_country_id(value: str) -> bool:
    """Whether value is the id of a country the game has a name for."""
    return value.isdigit() and bool(text.lookup_str("country", int(value)))


def _form_is_valid(form: dict[str, str]) -> bool:
    """Whether a sign-up form submission can become an account, apart from the username being free."""
    return (all(form.values())
            and USERNAME_PATTERN.fullmatch(form["username"]) is not None
            and not contains_bad_word(form["username"])
            and form["password"] == form["password_confirm"]
            and len(form["password"]) >= PASSWORD_MIN_LENGTH
            and len(form["email"]) <= EMAIL_MAX_LENGTH
            and EMAIL_PATTERN.fullmatch(form["email"]) is not None
            and _is_country_id(form["country"])
            and form["birth_month"] in BIRTH_MONTHS
            and form["pgl_privacy"] in PRIVACY_SETTINGS
            and form["dw_privacy"] in PRIVACY_SETTINGS)


@signup.route(SIGNUP_URL, methods=["GET", "POST"])
def trainer_club_signup() -> Response | WerkzeugResponse:
    """Show the Trainer Club sign-up form and handle its submission.

    GET shows the form. POST creates an unactivated account and emails its activation
    link. An invalid form just shows the form again.
    """
    if request.method == "GET":
        return serve_file(SIGNUP_DIR / "index.html")

    # strip spaces from all fields except passwords
    form = {field: request.form.get(field, "") if "password" in field else request.form.get(field, "").strip()
            for field in SIGNUP_FORM_FIELDS}

    if not _form_is_valid(form):
        return serve_file(SIGNUP_DIR / "index.html")

    activation_token = secrets.token_hex(16)

    created = accounts.create_account(
        username=form["username"],
        password_hash=generate_password_hash(form["password"]),
        email=form["email"],
        country=int(form["country"]),
        birth_month=int(form["birth_month"]),
        pgl_privacy=cast(Privacy, form["pgl_privacy"]),
        dw_privacy=cast(Privacy, form["dw_privacy"]),
        activation_token=activation_token,
    )
    if not created:  # the username is taken
        return serve_file(SIGNUP_DIR / "index.html")

    activation_url = request.host_url.rstrip("/") + ACTIVATION_URL.replace("<token>", activation_token)

    try:
        send_activation_email(form["email"], form["username"], activation_url, request.host_url)
    except (EmailNotConfiguredError, OSError, smtplib.SMTPException) as e:
        current_app.logger.warning("Could not send activation email: %s", e)

    return redirect(SIGNUP_URL + "confirmation.html")


@signup.get(ACTIVATION_URL)
def trainer_club_activate(token: str) -> Response | WerkzeugResponse:
    """Activate an account from the link in the activation email."""
    account = accounts.get_account_by_activation_token(token)
    if account is None:
        return not_found(request.path)

    accounts.activate_account(token)

    return redirect(SIGNUP_URL + "activated.html")
