"""
HTML email sender using smtplib + Jinja2.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from agent import config

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_alert_email(
    title: str,
    intro: str,
    skus: list,
    urgency_class: str,
    timestamp: str,
    narrative: str = "",
    subtitle: str = "",
) -> str:
    """Render the HTML email body from the template."""
    template = _env.get_template("email_alert.html")
    return template.render(
        title=title,
        subtitle=subtitle,
        intro=intro,
        skus=skus,
        urgency_class=urgency_class,
        narrative=narrative,
        timestamp=timestamp,
    )


def send_email(subject: str, plain_body: str, html_body: str, dry_run: bool = False) -> bool:
    """Send an HTML email via Gmail SMTP."""
    if dry_run:
        logger.info("[DRY RUN] Email: %s", subject)
        print(f"--- DRY RUN EMAIL ---\nSubject: {subject}\nHTML length: {len(html_body)} chars\n---------------------")
        return True

    if not config.NOTIFY_CHANNELS["email"]:
        logger.warning("Email not configured, skipping")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.GMAIL_USER
    msg["To"] = config.OWNER_EMAIL
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
            server.send_message(msg)
        logger.info("Email sent: %s", subject)
        return True
    except Exception as e:
        logger.error("Email failed: %s", e)
        return False