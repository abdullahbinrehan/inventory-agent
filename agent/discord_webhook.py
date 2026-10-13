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
    "SUCCESS":  0x10B981,  # green
    "ERROR":    0xEF4444,  # red
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
            "value": narrative[:1020],
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


def send_log_embed(
    source: str,
    duration_sec: float,
    summary: dict,
    timestamp: str,
    dry_run: bool = False,
) -> bool:
    """
    Send a structured run summary embed to #logs.

    summary keys: critical, digest, skipped
    """
    url = config.DISCORD_WEBHOOK_URL_LOGS

    if dry_run:
        print(f"[DRY RUN LOG EMBED] source={source} duration={duration_sec:.1f}s summary={summary}")
        return True

    if not url:
        return False

    total_alerted = summary.get("critical", 0) + summary.get("digest", 0)
    status_emoji = "⚠️" if total_alerted == 0 else "✅"

    embed = {
        "title": f"{status_emoji} Pipeline Run · {source}",
        "color": COLORS["SUCCESS"] if total_alerted > 0 else COLORS["LOGS"],
        "fields": [
            {"name": "🔴 Critical", "value": str(summary.get("critical", 0)), "inline": True},
            {"name": "🟠 Digest",   "value": str(summary.get("digest", 0)),   "inline": True},
            {"name": "⏭️ Skipped",  "value": str(summary.get("skipped", 0)),  "inline": True},
            {"name": "⏱️ Duration", "value": f"{duration_sec:.1f}s",           "inline": True},
            {"name": "🌐 Source",   "value": source,                          "inline": True},
            {"name": "🕒 Time",     "value": timestamp,                       "inline": True},
        ],
        "footer": {"text": "inventory-agent"},
    }

    payload = {"embeds": [embed]}

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info("Discord log embed sent")
        return True
    except Exception as e:
        logger.error("Discord log embed failed: %s", e)
        return False