"""
Data models for the inventory agent.

Each dataclass defines the exact shape of data as it moves through the pipeline:
  RawInventoryItem  -> what we get from an e-commerce API
  RawOrderLine      -> one line item from an order
  NormalizedSKU     -> merged + computed, ready for decisions
  AlertRecord       -> persisted history of past alerts
  Alert             -> final message ready to send
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# 1. Raw data from the e-commerce API
# ---------------------------------------------------------------------------

@dataclass
class RawInventoryItem:
    """One SKU's current stock, straight from the store API."""
    sku: str
    product_name: str
    current_stock: int
    location_id: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class RawOrderLine:
    """One line item from one order. An order with 3 products = 3 RawOrderLines."""
    order_id: str
    created_at: str          # ISO format string
    sku: str
    quantity: int
    price: float = 0.0


# ---------------------------------------------------------------------------
# 2. Normalized / computed data
# ---------------------------------------------------------------------------

@dataclass
class NormalizedSKU:
    """A SKU after merging inventory + sales and computing derived metrics."""
    sku: str
    product_name: str
    current_stock: int
    avg_daily_sales: float
    days_of_supply: float
    lead_time_days: int
    reorder_point: float
    suggested_reorder_qty: int
    urgency: str                       # "CRITICAL" | "HIGH" | "NORMAL" | "HEALTHY"

    # Phase B additions:
    sales_trend_pct: float = 0.0       # week-over-week % change (0.42 = +42%)
    spike_ratio: float = 1.0           # today's sales / 7-day average (1.0 = normal)
    category: str = ""                 # optional product category


# ---------------------------------------------------------------------------
# 3. Persisted alert history (for deduplication)
# ---------------------------------------------------------------------------

@dataclass
class AlertRecord:
    """One record of a past alert, used to avoid spamming the owner."""
    sku: str
    last_alerted_at: str
    urgency: str
    alert_count_7d: int = 1


# ---------------------------------------------------------------------------
# 4. Final alert message
# ---------------------------------------------------------------------------

@dataclass
class Alert:
    """A ready-to-send alert. Built by the composition layer."""
    title: str
    body: str
    urgency: str
    skus: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )