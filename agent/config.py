"""
Central configuration for the inventory agent.
Loads environment variables and defines constants used across the pipeline.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables from .env (local dev)
# On GitHub Actions, secrets come from the environment directly.
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATE_FILE = DATA_DIR / "state.json"
MOCK_INVENTORY_FILE = DATA_DIR / "mock_inventory.json"
MOCK_ORDERS_FILE = DATA_DIR / "mock_orders.json"


# ---------------------------------------------------------------------------
# Business logic constants
# ---------------------------------------------------------------------------
SALES_WINDOW_DAYS = 7
CRITICAL_THRESHOLD_DAYS = 3
HIGH_THRESHOLD_DAYS = 7
NORMAL_THRESHOLD_DAYS = 14
DEFAULT_LEAD_TIME_DAYS = 7
SAFETY_FACTOR = 1.5
DEDUP_WINDOW_HOURS = 24


# ---------------------------------------------------------------------------
# Secrets (loaded from environment; empty string if not set)
# ---------------------------------------------------------------------------
# Shopify (new Dev Dashboard system with client credentials)
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL", "")
SHOPIFY_CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID", "")
SHOPIFY_CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET", "")

# LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Email
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
OWNER_EMAIL = os.getenv("OWNER_EMAIL", "")

# Chat
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
DISCORD_WEBHOOK_URL_LOGS = os.getenv("DISCORD_WEBHOOK_URL_LOGS", "")


# ---------------------------------------------------------------------------
# Notification channels to enable
# ---------------------------------------------------------------------------
NOTIFY_CHANNELS = {
    "email": bool(GMAIL_USER and GMAIL_APP_PASSWORD and OWNER_EMAIL),
    "discord": bool(DISCORD_WEBHOOK_URL),
    "discord_logs": bool(DISCORD_WEBHOOK_URL_LOGS),
}