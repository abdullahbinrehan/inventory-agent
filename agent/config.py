import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATE_FILE = DATA_DIR / "state.json"
MOCK_INVENTORY_FILE = DATA_DIR / "mock_inventory.json"
MOCK_ORDERS_FILE = DATA_DIR / "mock_orders.json"

SALES_WINDOW_DAYS = 7
CRITICAL_THRESHOLD_DAYS = 3
HIGH_THRESHOLD_DAYS = 7
NORMAL_THRESHOLD_DAYS = 14
DEFAULT_LEAD_TIME_DAYS = 7
SAFETY_FACTOR = 1.5
DEDUP_WINDOW_HOURS = 24

SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL", "")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
OWNER_EMAIL = os.getenv("OWNER_EMAIL", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

NOTIFY_CHANNELS = {
    "email": bool(GMAIL_USER and GMAIL_APP_PASSWORD and OWNER_EMAIL),
    "discord": bool(DISCORD_WEBHOOK_URL),
}