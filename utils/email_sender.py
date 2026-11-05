"""The Trainer Club account activation email, sent over SMTP (see config.get_email_config)."""
import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import get_email_config

# served by api/server.py from dreamworld_assets/assets.pokemon.com
EMAIL_ASSETS_PATH = "assets.pokemon.com/static/_ui/img/email/basic"


def _render_activation_html(username: str, activation_url: str, assets_url: str) -> str:
    return f"""<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head>
<body>
<center>
<table border="0" cellspacing="0" cellpadding="0" width="590">
<tbody align="left">
<tr>
<td><img src="{assets_url}/header.jpg" width="590" height="74" alt="Pokémon"></td>
</tr>
<tr>
<td style="font-family:Arial,Helvetica,sans-serif;">
<table border="0" cellspacing="0" cellpadding="20" width="590">
<tbody align="left">
<tr>
<td style="font-family:Arial,Helvetica,sans-serif;">
<p><font face="Arial" size="2">
<p style="margin:0;padding:0"><img src="{assets_url}/Email_Template_04.gif" width="164" height="176" alt="" valign="top" align="right"></p>
Dear {html.escape(username)},<br><br>
You're almost ready to access all the features of the Pokémon Global Link! To activate your account, click on the button below.
</font></p>
<p><font face="Arial" size="3" color="#00a8ff">
<br>
<p style="margin:0;padding:0">
<a href="{html.escape(activation_url)}">
<img src="{assets_url}/activate.png" border="0" width="328" height="35" alt="Activate Your Account">
</a></p>
</font></p>
<p><font face="Arial" size="2"></font></p>
<p><font face="Arial" size="2">Sincerely,<br>
<b>The Pokémon Company, Inc. USA</b></font></p>
</td>
</tr>
</tbody>
</table>
</td>
</tr>
<tr>
<td width="590" bgcolor="#5b5b5b">
<table border="0" cellspacing="5" cellpadding="5">
<tbody align="left">
<tr>
<td><img src="{assets_url}/po-co.png" width="172" height="19" alt="The Pokémon Company"></td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
</center>
</body>
</html>"""


def send_activation_email(to_email: str, username: str, activation_url: str, site_url: str) -> None:
    """Send the Trainer Club activation email over the configured Gmail account.

    `site_url` is this server's address (e.g. request.host_url). Raises
    EmailNotConfiguredError, OSError, or smtplib.SMTPException if it can't
    be sent.
    """
    config = get_email_config()
    assets_url = f"{site_url.rstrip('/')}/{EMAIL_ASSETS_PATH}"

    text_body = (
        f"You're almost ready to access all the features of the Pokémon Global Link!\n"
        f"To activate your account, visit the link below:\n\n"
        f"{activation_url}\n\n"
        f"Sincerely,\nThe Pokémon Company, Inc. USA"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Pokémon Trainer Club Activation"
    msg["From"] = config["smtp_address"]
    msg["To"] = to_email
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(_render_activation_html(username, activation_url, assets_url), "html"))

    with smtplib.SMTP(config["smtp_host"], config["smtp_port"]) as server:
        server.starttls()
        server.login(config["smtp_address"], config["smtp_app_password"])
        server.sendmail(config["smtp_address"], to_email, msg.as_string())
