import logging
import requests

logger = logging.getLogger(__name__)

COLORS = {"CRITICAL": 0xEF4444, "HIGH": 0xF59E0B, "NORMAL": 0x3B82F6, "HEALTHY": 0x10B981, "LOGS": 0x6B7280, "SUCCESS": 0x10B981, "ERROR": 0xEF4444}

def _build_embed(title: str, description: str, skus: list, urgency: str, narrative: str = "") -> dict:
    color = COLORS.get(urgency, COLORS["LOGS"])
    fields = [{"name": f"{s.product_name} · {s.urgency}", "value": f"**SKU:** `{s.sku}`\n**Stock:** {s.current_stock} · **Supply:** {s.days_of_supply}d · **Reorder:** {s.suggested_reorder_qty} units", "inline": False} for s in skus]
    embed = {"title": title, "description": description, "color": color, "fields": fields, "footer": {"text": "inventory-agent"}}
    if narrative: embed["fields"].append({"name": "📝 Summary", "value": narrative[:1020], "inline": False})
    return embed

def send_embed(title: str, description: str, skus: list, urgency: str, user_config: dict, narrative: str = "", dry_run: bool = False) -> bool:
    url = user_config.get("discord_webhook_url")
    if dry_run:
        print(f"--- DRY RUN DISCORD ---\n{title}\nSKUs: {len(skus)}\n-----------------------")
        return True
    if not url: return False
    try:
        resp = requests.post(url, json={"embeds": [_build_embed(title, description, skus, urgency, narrative)]}, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Discord send failed: %s", e)
        return False

def send_log_embed(source: str, duration_sec: float, summary: dict, timestamp: str, user_config: dict, dry_run: bool = False) -> bool:
    url = user_config.get("discord_webhook_url_logs")
    if dry_run: return True
    if not url: return False
    
    total_alerted = summary.get("critical", 0) + summary.get("digest", 0)
    embed = {
        "title": f"{'⚠️' if total_alerted == 0 else '✅'} Pipeline Run · {source}",
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
    try:
        resp = requests.post(url, json={"embeds": [embed]}, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Discord log embed failed: %s", e)
        return False

def send_log_message(message: str, user_config: dict, dry_run: bool = False) -> bool:
    """Send a plain text message (used for error tracebacks)"""
    url = user_config.get("discord_webhook_url_logs")
    if dry_run: return True
    if not url: return False
    try:
        resp = requests.post(url, json={"content": message}, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Discord log message failed: %s", e)
        return False