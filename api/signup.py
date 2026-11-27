"""Trainer Club sign-up and account activation."""
import json
import re
import secrets
import smtplib
from pathlib import Path
from typing import cast, get_args

from flask import Blueprint, Response, current_app, redirect, request
from werkzeug.security import generate_password_hash
from werkzeug.wrappers import Response as WerkzeugResponse

from config import SUPPORTED_LANGUAGES, EmailNotConfiguredError
from utils import text
from utils.account_manager import accounts
from utils.assets import ASSETS_DIR, not_found, serve_file
from utils.badwords import contains_bad_word
from utils.email_sender import send_activation_email
from utils.messages import message
from utils.models import Privacy

SIGNUP_LANGUAGES = ("en", "de")
PLACEHOLDER_SIGNUP_LANGUAGE = "en"
_LANG = f"<any({','.join(SUPPORTED_LANGUAGES)}):lang>"  # other values get a 404
SIGNUP_ROUTE     = f"/www.pokemon.com/{_LANG}/account/pgl/signup/"
ACTIVATION_ROUTE = f"/www.pokemon.com/{_LANG}/account/pgl/activated/<token>"

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


def signup_url(lang: str) -> str:
    """Return the URL of a sign-up page."""
    return f"/www.pokemon.com/{lang}/account/pgl/signup/"


def activation_url(lang: str, token: str) -> str:
    """Return the URL of an activation link."""
    return f"/www.pokemon.com/{lang}/account/pgl/activated/{token}"


def _signup_dir(lang: str) -> Path:
    return ASSETS_DIR / "www.pokemon.com" / lang / "account" / "pgl" / "signup"


def _placeholder_redirect(lang: str, url: str) -> WerkzeugResponse | None:
    """Send a language without its own sign-up page yet to the placeholder `url`."""
    return None if lang in SIGNUP_LANGUAGES else redirect(url)


def _is_country_id(value: str) -> bool:
    """Whether value is the id of a country the game has a name for."""
    return value.isdigit() and bool(text.lookup_str("country", int(value)))


def _field_error(field: str, value: str, form: dict[str, str]) -> str | None:
    """Return the message id for what is wrong with a field of the sign-up form."""
    if not value:
        return "missing_field"
    match field:
        case "country":
            return None if _is_country_id(value) else "bad_choice"
        case "birth_month":
            return None if value in BIRTH_MONTHS else "bad_choice"
        case "pgl_privacy" | "dw_privacy":
            return None if value in PRIVACY_SETTINGS else "bad_choice"
        case "username":
            if USERNAME_PATTERN.fullmatch(value) is None:
                return "bad_username"
            return "bad_username_word" if contains_bad_word(value) else None
        case "password":
            return None if len(value) >= PASSWORD_MIN_LENGTH else "password_too_short"
        case "password_confirm":
            return None if value == form["password"] else "password_mismatch"
        case "email":
            valid = len(value) <= EMAIL_MAX_LENGTH and EMAIL_PATTERN.fullmatch(value) is not None
            return None if valid else "bad_email"
    return None


def _form_errors(form: dict[str, str], lang: str | None = None) -> dict[str, str]:
    """Returns what's wrong with the form submission.

    Returns an empty dict is nothing is wrong.
    """
    errors = {}
    for field, value in form.items():
        message_id = _field_error(field, value, form)
        if message_id:
            errors[field] = message(message_id, lang, length=PASSWORD_MIN_LENGTH)
    return errors


def _form_with_errors(form: dict[str, str], errors: dict[str, str], lang: str) -> Response:
    """Return the sign-up form (400) with the player's entries and what's wrong with them."""
    result = {
        "alert":  message("signup_has_errors", lang),
        "errors": errors,
        "values": {field: value for field, value in form.items() if "password" not in field},
    }
    # escape <, >, and &
    data = json.dumps(result).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    response = serve_file(_signup_dir(lang) / "index.html")
    page = response.get_data(as_text=True)
    response.set_data(page.replace("</head>", f"<script>window.SIGNUP_RESULT = {data};</script>\n</head>", 1))
    response.status_code = 400
    return response


@signup.route(SIGNUP_ROUTE, methods=["GET", "POST"])
def trainer_club_signup(lang: str) -> Response | WerkzeugResponse:
    """Show the Trainer Club sign-up form and handle its submission.

    GET shows the form. POST creates an unactivated account and emails its activation
    link.
    """
    if other := _placeholder_redirect(lang, signup_url(PLACEHOLDER_SIGNUP_LANGUAGE)):
        return other
    if request.method == "GET":
        return serve_file(_signup_dir(lang) / "index.html")

    # strip spaces from all fields except passwords
    form = {field: request.form.get(field, "") if "password" in field else request.form.get(field, "").strip()
            for field in SIGNUP_FORM_FIELDS}

    errors = _form_errors(form, lang)
    if errors:
        return _form_with_errors(form, errors, lang)

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
    if not created:
        return _form_with_errors(form, {"username": message("username_taken", lang)}, lang)

    activation_link = request.host_url.rstrip("/") + activation_url(lang, activation_token)

    try:
        send_activation_email(form["email"], activation_link)
    except (EmailNotConfiguredError, OSError, smtplib.SMTPException) as e:
        current_app.logger.warning("Could not send activation email: %s", e)

    return redirect(signup_url(lang) + "confirmation.html")


@signup.get(ACTIVATION_ROUTE)
def trainer_club_activate(lang: str, token: str) -> Response | WerkzeugResponse:
    """Activate an account from the link in the activation email."""
    if other := _placeholder_redirect(lang, activation_url(PLACEHOLDER_SIGNUP_LANGUAGE, token)):
        return other
    account = accounts.get_account_by_activation_token(token)
    if account is None:
        return not_found(request.path)

    accounts.activate_account(token)

    return redirect(signup_url(lang) + "activated.html")
