"""
State layer.

Persists a record of which SKUs were alerted and when, so we don't spam
the owner with the same alert every run. State is stored as JSON.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent import config
from agent.models import AlertRecord

# Urgency ranking — higher number = more urgent.
URGENCY_RANK = {
    "HEALTHY": 0,
    "NORMAL": 1,
    "HIGH": 2,
    "CRITICAL": 3,
}


# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------

def load_state(path: Path = config.STATE_FILE) -> dict:
    """Read state.json. Returns empty dict if file missing or corrupt."""
    if not path.exists():
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict, path: Path = config.STATE_FILE) -> None:
    """Write state.json, creating parent dir if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# Deduplication logic
# ---------------------------------------------------------------------------

def _parse_iso(ts: str) -> datetime:
    """Parse an ISO timestamp into an aware datetime."""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def should_alert(sku: str, urgency: str, state: dict) -> bool:
    """
    Decide whether to alert for this SKU right now.

    Returns True if:
      - We've never alerted this SKU, OR
      - Last alert was more than DEDUP_WINDOW_HOURS ago, OR
      - Urgency has escalated since last alert.
    """
    record = state.get(sku)
    if not record:
        return True

    last_at = _parse_iso(record["last_alerted_at"])
    now = datetime.now(timezone.utc)
    hours_since = (now - last_at).total_seconds() / 3600

    if hours_since >= config.DEDUP_WINDOW_HOURS:
        return True

    last_urgency = record.get("urgency", "HEALTHY")
    if URGENCY_RANK.get(urgency, 0) > URGENCY_RANK.get(last_urgency, 0):
        return True

    return False


def record_alert(sku: str, urgency: str, state: dict) -> None:
    """Update the state dict to reflect that we just alerted for this SKU."""
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    existing = state.get(sku)

    if existing and _within_7_days(existing.get("last_alerted_at", "")):
        count = existing.get("alert_count_7d", 0) + 1
    else:
        count = 1

    state[sku] = {
        "sku": sku,
        "last_alerted_at": now_iso,
        "urgency": urgency,
        "alert_count_7d": count,
    }


def _within_7_days(ts: str) -> bool:
    """True if timestamp is within the last 7 days."""
    try:
        return datetime.now(timezone.utc) - _parse_iso(ts) < timedelta(days=7)
    except (ValueError, TypeError):
        return False