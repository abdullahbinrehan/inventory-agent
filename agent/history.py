"""
Run history CSV writer.

Appends one row per pipeline run to docs/run_history.csv.
The file is committed back to the repo by GitHub Actions and served
by GitHub Pages as part of the dashboard.
"""

import csv
import logging
from datetime import datetime, timezone

from agent import config

logger = logging.getLogger(__name__)

HISTORY_FILE = config.PROJECT_ROOT / "docs" / "run_history.csv"

HEADERS = [
    "date",
    "source",
    "total_skus",
    "alertable",
    "critical",
    "digest",
    "duration_sec",
]


def append_run(
    source: str,
    total_skus: int,
    alertable: int,
    summary: dict,
    duration_sec: float,
    dry_run: bool = False,
) -> bool:
    """
    Append one row to docs/run_history.csv. Never raises.

    Creates the file with headers if it doesn't exist.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    row = [
        ts,
        source,
        total_skus,
        alertable,
        summary.get("critical", 0),
        summary.get("digest", 0),
        round(duration_sec, 2),
    ]

    if dry_run:
        print(f"[DRY RUN HISTORY] would append: {row}")
        return True

    try:
        file_exists = HISTORY_FILE.exists()
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(HEADERS)
            writer.writerow(row)

        logger.info("Appended run row to %s", HISTORY_FILE)
        return True
    except Exception as e:
        logger.error("Failed to append to history CSV: %s", e)
        return False