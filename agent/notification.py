"""
Notification layer.

Routes alerts to HTML email + Discord rich embed.
Also exposes legacy send_alert() for simple test messages.
"""

import logging
from datetime import datetime, timezone

import apprise

from agent import config
from agent.discord_webhook import send_embed
from agent.emailer import render_alert_email, send_email

logger = logging.getLogger(__name__)


def build_apprise_client() -> apprise.Apprise:
    """Kept for the simple send_alert() path."""
    apobj = apprise.Apprise()
    if config.NOTIFY_CHANNELS["email"]:
        url = (
            f"mailtos://smtp.gmail.com:587"
            f"?user={config.GMAIL_USER}"
            f"&pass={config.GMAIL_APP_PASSWORD}"
            f"&from={config.GMAIL_USER}"
            f"&to={config.OWNER_EMAIL}"
        )
        apobj.add(url)
    if config.NOTIFY_CHANNELS["discord"]:
        apobj.add(config.DISCORD_WEBHOOK_URL)
    return apobj


def send_alert(title: str, body: str, dry_run: bool = False) -> bool:
    """Simple plain-text send. Used for tests and one-off messages."""
    if dry_run:
        logger.info("[DRY RUN] %s", title)
        print(f"--- DRY RUN ---\n{title}\n\n{body}\n---------------")
        return True

    apobj = build_apprise_client()
    if len(apobj) == 0:
        logger.warning("No notification channels configured")
        return False

    try:
        return apobj.notify(title=title, body=body)
    except Exception as e:
        logger.error("Notification error: %s", e)
        return False


def send_rich_alert(
    title: str,
    subtitle: str,
    intro: str,
    skus: list,
    urgency: str,
    narrative: str = "",
    dry_run: bool = False,
) -> dict:
    """
    Send an alert to all configured channels with rich formatting.

    Returns a dict like {"email": True, "discord": True}.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    urgency_class = "critical" if urgency == "CRITICAL" else "digest"

    html_body = render_alert_email(
        title=title,
        subtitle=subtitle,
        intro=intro,
        skus=skus,
        urgency_class=urgency_class,
        timestamp=ts,
        narrative=narrative,
    )

    plain_body = f"{title}\n\n{intro}\n\n" + "\n".join(
        f"- {s.product_name} ({s.sku}): {s.current_stock} in stock, "
        f"{s.days_of_supply}d supply, reorder {s.suggested_reorder_qty}"
        for s in skus
    )
    if narrative:
        plain_body += f"\n\nSummary: {narrative}"

    results = {
        "email": send_email(title, plain_body, html_body, dry_run=dry_run),
        "discord": send_embed(
            title=title,
            description=intro,
            skus=skus,
            urgency=urgency,
            narrative=narrative,
            dry_run=dry_run,
        ),
    }
    return results