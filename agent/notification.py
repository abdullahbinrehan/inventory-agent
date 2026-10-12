"""
Notification layer.

Sends alerts through Apprise. Channels are configured via .env.
"""

import logging

import apprise

from agent import config

logger = logging.getLogger(__name__)


def build_apprise_client() -> apprise.Apprise:
    """Build an Apprise client with all enabled channels."""
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
    """Build an Apprise client with all enabled channels."""
    apobj = apprise.Apprise()

    if config.NOTIFY_CHANNELS["email"]:
        apobj.add(
            f"mailtos://{config.GMAIL_USER}:{config.GMAIL_APP_PASSWORD}"
            f"@gmail.com?to={config.OWNER_EMAIL}"
        )

    if config.NOTIFY_CHANNELS["discord"]:
        apobj.add(config.DISCORD_WEBHOOK_URL)

    return apobj


def send_alert(title: str, body: str, dry_run: bool = False) -> bool:
    """
    Send a single notification.

    Returns True on success, False on failure. Never raises.
    """
    if dry_run:
        logger.info("[DRY RUN] Would send: %s", title)
        print(f"--- DRY RUN ---\n{title}\n\n{body}\n---------------")
        return True

    apobj = build_apprise_client()
    if len(apobj) == 0:
        logger.warning("No notification channels configured — skipping send")
        return False

    try:
        ok = apobj.notify(title=title, body=body)
        if ok:
            logger.info("Sent notification: %s", title)
        else:
            logger.error("Notification failed: %s", title)
        return ok
    except Exception as e:
        logger.error("Notification error: %s", e)
        return False