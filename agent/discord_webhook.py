"""
Discord webhook sender with rich embeds.
"""

import logging

import requests

from agent import config

logger = logging.getLogger(__name__)

# Discord embed sidebar colors (hex integers)
COLORS = {
    "CRITICAL": 0xEF4444,  # red
    "HIGH":     0xF59E0B,  # amber
    "NORMAL":   0x3B82F6,  # blue
    "HEALTHY":  0x10B981,  # green
    "LOGS":     0x6B7280,  # gray
}


def _build_embed(
    title: str,
    description: str,
    skus: list,
    urgency: str,
    narrative: str = "",
) -> dict:
    """Build the Discord embed JSON payload."""
    color = COLORS.get(urgency, COLORS["LOGS"])

    fields = []
    for s in skus:
        fields.append({
            "name": f"{s.product_name} · {s.urgency}",
            "value": (
                f"**SKU:** `{s.sku}`\n"
                f"**Stock:** {s.current_stock} · "
                f"**Supply:** {s.days_of_supply}d · "
                f"**Reorder:** {s.suggested_reorder_qty} units"
            ),
            "inline": False,
        })

    embed = {
        "title": title,
        "description": description,
        "color": color,
        "fields": fields,
        "footer": {"text": "inventory-agent"},
    }

    if narrative:
        embed["fields"].append({
            "name": "📝 Summary",
            "value": narrative[:1020],  # Discord field value limit is 1024
            "inline": False,
        })

    return embed


def send_embed(
    title: str,
    description: str,
    skus: list,
    urgency: str,
    narrative: str = "",
    webhook_url: str = "",
    dry_run: bool = False,
) -> bool:
    """Send a rich embed to Discord via webhook."""
    url = webhook_url or config.DISCORD_WEBHOOK_URL

    if dry_run:
        logger.info("[DRY RUN] Discord embed: %s", title)
        print(f"--- DRY RUN DISCORD ---\n{title}\n{description}\nSKUs: {len(skus)}\n-----------------------")
        return True

    if not url:
        logger.warning("Discord webhook not configured, skipping")
        return False

    payload = {"embeds": [_build_embed(title, description, skus, urgency, narrative)]}

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info("Discord embed sent: %s", title)
        return True
    except Exception as e:
        logger.error("Discord send failed: %s", e)
        return False


def send_log(message: str, dry_run: bool = False) -> bool:
    """Send a plain text line to the #logs channel."""
    if dry_run:
        print(f"[DRY RUN LOG] {message}")
        return True

    url = config.DISCORD_WEBHOOK_URL_LOGS
    if not url:
        return False

    try:
        resp = requests.post(url, json={"content": message}, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Discord log failed: %s", e)
        return False