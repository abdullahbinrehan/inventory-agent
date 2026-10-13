"""
Heartbeat / health check.

Runs on a separate schedule. Checks whether the daily inventory pipeline
has run successfully in the last N hours. Alerts if stale.
"""

import argparse
import logging
import os
from datetime import datetime, timezone

import requests

from agent.discord_webhook import send_log

logger = logging.getLogger(__name__)

STALE_HOURS = 36
WORKFLOW_FILE = "daily_run.yml"


def _parse_iso(ts: str) -> datetime:
    """Parse an ISO timestamp into an aware datetime (UTC if naive)."""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def fetch_last_successful_run(repo: str, token: str) -> datetime | None:
    """Query GitHub API for the latest successful daily_run."""
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{WORKFLOW_FILE}/runs"
    params = {"status": "success", "per_page": 1}
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    runs = resp.json().get("workflow_runs", [])
    if not runs:
        return None
    return _parse_iso(runs[0]["created_at"])


def check_heartbeat(repo: str, token: str, stale_hours: int = STALE_HOURS) -> tuple[bool, float]:
    """
    Returns (is_stale, hours_since_last_success).
    If no successful run exists, returns (True, inf).
    """
    last = fetch_last_successful_run(repo, token)
    if last is None:
        return True, float("inf")
    hours = (datetime.now(timezone.utc) - last).total_seconds() / 3600
    return hours >= stale_hours, hours


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Heartbeat check")
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--stale-hours", type=int, default=STALE_HOURS)
    args = parser.parse_args()

    token = os.getenv("GH_TOKEN", "")
    if not token:
        logger.error("GH_TOKEN not set — cannot query GitHub API")
        return

    stale, hours = check_heartbeat(args.repo, token, args.stale_hours)

    if stale:
        if hours == float("inf"):
            msg = "⚠️ **Heartbeat:** No successful pipeline run found on record."
        else:
            msg = f"⚠️ **Heartbeat:** Last successful run was {hours:.1f}h ago (threshold: {args.stale_hours}h)."
        logger.warning(msg)
        send_log(msg)
    else:
        logger.info("Heartbeat OK — last successful run %.1fh ago", hours)


if __name__ == "__main__":
    main()