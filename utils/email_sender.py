"""The Trainer Club account activation email, sent over SMTP (see config.get_email_config)."""
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

from config import get_email_config

SENDER_NAME = "Dream World Reawakened"


def send_activation_email(to_email: str, activation_url: str) -> None:
    """Send the account activation email over the configured SMTP account.

    Raises EmailNotConfiguredError, OSError, or smtplib.SMTPException if it can't be sent.
    """
    config = get_email_config()

    msg = MIMEText(f"Here is your activation link for Dream World Reawakened: {activation_url}", "plain", "utf-8")
    msg["Subject"] = "Dream World Reawakened account activation"
    msg["From"] = formataddr((SENDER_NAME, config["smtp_address"]))
    msg["To"] = to_email

    with smtplib.SMTP(config["smtp_host"], config["smtp_port"]) as server:
        server.starttls()
        # Gmail logs in with the address, but services like Resend use a separate username
        server.login(config.get("smtp_username") or config["smtp_address"], config["smtp_app_password"])
        server.sendmail(config["smtp_address"], to_email, msg.as_string())
