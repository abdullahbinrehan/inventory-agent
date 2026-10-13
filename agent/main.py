"""
Orchestrator. Runs the full pipeline end-to-end.

Usage:
    python -m agent.main --source mock --dry-run
    python -m agent.main --source shopify
"""

import argparse
import logging
import time
from datetime import datetime, timezone

from agent import config
from agent.analysis import filter_alertable, normalize_all
from agent.composition import compose_critical_alert, compose_daily_digest
from agent.discord_webhook import send_log_embed
from agent.error_handler import send_error_alert
from agent.history import append_run
from agent.ingestion import get_inventory, get_orders
from agent.notification import send_rich_alert
from agent.state import load_state, record_alert, save_state, should_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agent.main")


def run_pipeline(source: str = "mock", dry_run: bool = False, force: bool = False) -> dict:
    """Run the entire pipeline. Returns a summary dict."""
    started_at = time.time()
    logger.info("Starting pipeline | source=%s dry_run=%s force=%s", source, dry_run, force)

    # 1. Load state
    state = load_state()

    # 2. Fetch
    inventory = get_inventory(source)
    orders = get_orders(source)
    logger.info("Fetched %d inventory items, %d order lines", len(inventory), len(orders))

    # 3. Analyze
    normalized = normalize_all(inventory, orders)
    alertable = filter_alertable(normalized)
    logger.info("Alertable SKUs: %d", len(alertable))

    # 4. Dedup
    if force:
        to_alert = alertable
        logger.info("Force mode — ignoring dedup, alerting %d SKUs", len(to_alert))
    else:
        to_alert = [s for s in alertable if should_alert(s.sku, s.urgency, state)]
        logger.info("After dedup: %d SKUs need alerts", len(to_alert))

    # 5. Split into critical vs digest
    critical = [s for s in to_alert if s.urgency == "CRITICAL"]
    digest_items = [s for s in to_alert if s.urgency in ("HIGH", "NORMAL")]

    summary = {"critical": 0, "digest": 0, "skipped": len(alertable) - len(to_alert)}

    # 6. Compose + send critical
    if critical:
        body = compose_critical_alert(critical)
        title = f"🚨 CRITICAL · {len(critical)} SKU(s) need restocking"
        send_rich_alert(
            title=title,
            subtitle="Immediate action required",
            intro=f"{len(critical)} SKU(s) are critically low and need restocking now.",
            skus=critical,
            urgency="CRITICAL",
            narrative=body,
            dry_run=dry_run,
        )
        if not dry_run:
            for s in critical:
                record_alert(s.sku, s.urgency, state)
        summary["critical"] = len(critical)

    # 7. Compose + send digest
    if digest_items:
        body = compose_daily_digest(digest_items)
        title = f"📦 Daily Digest · {len(digest_items)} SKU(s) to watch"
        send_rich_alert(
            title=title,
            subtitle="No action needed immediately",
            intro=f"{len(digest_items)} SKU(s) are trending low — keep an eye on them.",
            skus=digest_items,
            urgency="NORMAL",
            narrative=body,
            dry_run=dry_run,
        )
        if not dry_run:
            for s in digest_items:
                record_alert(s.sku, s.urgency, state)
        summary["digest"] = len(digest_items)

    # 8. Save state
    if not dry_run:
        save_state(state)
        logger.info("State saved to %s", config.STATE_FILE)

    # 9. Append a row to run history CSV
    duration = time.time() - started_at
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    append_run(
        source=source,
        total_skus=len(normalized),
        alertable=len(alertable),
        summary=summary,
        duration_sec=duration,
        dry_run=dry_run,
    )

    # 10. Send structured log embed to Discord #logs
    logger.info("Pipeline done in %.1fs | %s", duration, summary)

    send_log_embed(
        source=source,
        duration_sec=duration,
        summary=summary,
        timestamp=ts,
        dry_run=dry_run,
    )

    return summary


def run_pipeline_safe(source: str = "mock", dry_run: bool = False, force: bool = False) -> dict | None:
    """
    Wrapper around run_pipeline() that catches exceptions, sends an error
    alert, and re-raises so the process still exits with a non-zero code.
    """
    try:
        return run_pipeline(source=source, dry_run=dry_run, force=force)
    except Exception as e:
        logger.exception("Pipeline crashed")
        send_error_alert(e)
        raise


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Inventory agent pipeline")
    p.add_argument("--source", choices=["mock", "shopify"], default="mock")
    p.add_argument("--dry-run", action="store_true",
                   help="Do not send or persist; just print")
    p.add_argument("--force", action="store_true",
                   help="Ignore dedup window — alert everything alertable")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_pipeline_safe(source=args.source, dry_run=args.dry_run, force=args.force)