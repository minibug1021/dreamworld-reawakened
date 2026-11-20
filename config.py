"""Server-wide settings and paths.

Importing this module touches no files, but it does raise ValueError if DW_LANG isn't a
supported language.
"""
import getpass
import json
import os
import secrets
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

# The game_sync_server submodule reads the same variable (game_sync_server/.../db_manager.py).
SAVE_DIR = Path(os.environ.get("DW_SAVE_DIR", ROOT_DIR / "save_data"))
SECRET_KEY_PATH = SAVE_DIR / "flask_secret_key.txt"
EMAIL_CONFIG_PATH = ROOT_DIR / "email_config.json"

SUPPORTED_LANGUAGES = ("ja", "en", "fr", "it", "de", "es", "ko")
DEFAULT_LANGUAGE = "en"

# The site language for visitors who haven't picked one. Set it with the DW_LANG
# environment variable or `main.py --lang`.
DEFAULT_SITE_LANGUAGE = os.environ.get("DW_LANG", DEFAULT_LANGUAGE)
if DEFAULT_SITE_LANGUAGE not in SUPPORTED_LANGUAGES:
    raise ValueError(f"DW_LANG must be one of {', '.join(SUPPORTED_LANGUAGES)}, not {DEFAULT_SITE_LANGUAGE!r}")


def get_secret_key() -> str:
    """Flask's session-signing key, created in the save directory on first use."""
    SECRET_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SECRET_KEY_PATH.exists():
        SECRET_KEY_PATH.write_text(secrets.token_hex(32))
    return SECRET_KEY_PATH.read_text().strip()


_EMAIL_CONFIG_TEMPLATE = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_address": "your_email@gmail.com",
    "smtp_app_password": "your_app_password",
}


class EmailNotConfiguredError(Exception):
    """email_config.json is missing or still has its placeholder values."""


def get_email_config(prompt: bool = False) -> dict:
    """SMTP settings from email_config.json.

    If the file doesn't exist yet, a template is written. With prompt=True the Gmail
    address and app password are then asked for on the terminal.

    Raises EmailNotConfiguredError if there are no usable settings.
    """
    if not EMAIL_CONFIG_PATH.is_file():
        EMAIL_CONFIG_PATH.write_text(json.dumps(_EMAIL_CONFIG_TEMPLATE, indent=4) + "\n")
        if not prompt:
            raise EmailNotConfiguredError(
                f"No email config found - created {EMAIL_CONFIG_PATH}. Fill in your Gmail address and "
                "app password there to enable sending activation emails."
            )

        # interactive setup prompt, so plain print rather than logging
        print(f"\nNo email config found - creating {EMAIL_CONFIG_PATH}.")
        print("This is used to send Trainer Club account activation emails over Gmail.")
        print("Generate an app password at https://myaccount.google.com/apppasswords, then enter it below.\n")
        try:
            address = input("Gmail address: ").strip()
            app_password = getpass.getpass("App password: ").strip()
        except EOFError:
            address = app_password = ""

        if not address or not app_password:
            raise EmailNotConfiguredError(
                f"No email address/app password entered. Fill them in manually in {EMAIL_CONFIG_PATH} "
                "to enable sending activation emails."
            )

        config = {**_EMAIL_CONFIG_TEMPLATE, "smtp_address": address, "smtp_app_password": app_password}
        EMAIL_CONFIG_PATH.write_text(json.dumps(config, indent=4) + "\n")
        return config

    config = json.loads(EMAIL_CONFIG_PATH.read_text())
    if (config.get("smtp_address") == _EMAIL_CONFIG_TEMPLATE["smtp_address"]
            or config.get("smtp_app_password") == _EMAIL_CONFIG_TEMPLATE["smtp_app_password"]):
        raise EmailNotConfiguredError(
            f"{EMAIL_CONFIG_PATH} still has placeholder values, fill in your Gmail address and app password."
        )
    return config
