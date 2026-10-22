import logging
from datetime import datetime, timezone

from agent.discord_webhook import send_embed
from agent.emailer import render_alert_email, send_email

logger = logging.getLogger(__name__)

def send_rich_alert(title: str, subtitle: str, intro: str, skus: list, urgency: str, user_config: dict, narrative: str = "", dry_run: bool = False) -> dict:
    """Send an alert to email and Discord using the user's specific credentials."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    urgency_class = "critical" if urgency == "CRITICAL" else "digest"
    
    html_body = render_alert_email(
        title=title, 
        subtitle=subtitle, 
        intro=intro, 
        skus=skus, 
        urgency_class=urgency_class, 
        timestamp=ts, 
        narrative=narrative
    )
    
    plain_body = f"{title}\n\n{intro}\n\n" + "\n".join(
        f"- {s.product_name} ({s.sku}): {s.current_stock} in stock, {s.days_of_supply}d supply, reorder {s.suggested_reorder_qty}" 
        for s in skus
    )
    if narrative: 
        plain_body += f"\n\nSummary: {narrative}"

    return {
        "email": send_email(title, plain_body, html_body, user_config, dry_run=dry_run),
        "discord": send_embed(
            title=title, 
            description=intro, 
            skus=skus, 
            urgency=urgency, 
            user_config=user_config, 
            narrative=narrative, 
            dry_run=dry_run
        ),
    }