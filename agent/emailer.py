import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "xml"]))

def render_alert_email(title: str, intro: str, skus: list, urgency_class: str, timestamp: str, narrative: str = "", subtitle: str = "") -> str:
    template = _env.get_template("email_alert.html")
    return template.render(title=title, subtitle=subtitle, intro=intro, skus=skus, urgency_class=urgency_class, narrative=narrative, timestamp=timestamp)

def send_email(subject: str, plain_body: str, html_body: str, user_config: dict, dry_run: bool = False) -> bool:
    if dry_run:
        print(f"--- DRY RUN EMAIL ---\nSubject: {subject}\nHTML length: {len(html_body)} chars\n---------------------")
        return True

    if not user_config.get("gmail_user") or not user_config.get("gmail_app_password"):
        logger.warning("Email not configured for user")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user_config["gmail_user"]
    msg["To"] = user_config.get("owner_email") or user_config["gmail_user"]
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(user_config["gmail_user"], user_config["gmail_app_password"])
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error("Email failed: %s", e)
        return False