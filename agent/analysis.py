"""
Analysis engine.

Takes raw inventory + order lines and produces NormalizedSKU objects with
computed metrics and an urgency tier. Pure Python, no LLM.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from math import inf

from agent import config
from agent.models import RawInventoryItem, RawOrderLine, NormalizedSKU


# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------

def compute_avg_daily_sales(
    orders: list[RawOrderLine],
    sku: str,
    window_days: int = config.SALES_WINDOW_DAYS,
) -> float:
    """Sum quantities sold for a SKU over the window, divided by window_days."""
    if window_days <= 0:
        return 0.0
    total_qty = sum(o.quantity for o in orders if o.sku == sku)
    return total_qty / window_days


def compute_days_of_supply(current_stock: int, avg_daily_sales: float) -> float:
    """
    How many days until stockout at current sales rate.
    Returns inf if sales are zero (dead stock — no urgency).
    """
    if avg_daily_sales <= 0:
        return inf
    return current_stock / avg_daily_sales


def compute_reorder_point(
    avg_daily_sales: float,
    lead_time_days: int = config.DEFAULT_LEAD_TIME_DAYS,
    safety_factor: float = config.SAFETY_FACTOR,
) -> float:
    """Stock level at which we should place a new order."""
    return avg_daily_sales * lead_time_days * safety_factor


def compute_suggested_reorder_qty(
    avg_daily_sales: float,
    lead_time_days: int = config.DEFAULT_LEAD_TIME_DAYS,
    safety_factor: float = config.SAFETY_FACTOR,
) -> int:
    """How many units to reorder."""
    qty = avg_daily_sales * lead_time_days * safety_factor
    return max(0, round(qty))


def classify_urgency(days_of_supply: float) -> str:
    """Map days_of_supply to an urgency tier."""
    if days_of_supply == inf:
        return "HEALTHY"
    if days_of_supply < config.CRITICAL_THRESHOLD_DAYS:
        return "CRITICAL"
    if days_of_supply < config.HIGH_THRESHOLD_DAYS:
        return "HIGH"
    if days_of_supply < config.NORMAL_THRESHOLD_DAYS:
        return "NORMAL"
    return "HEALTHY"


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize_sku(
    item: RawInventoryItem,
    orders: list[RawOrderLine],
) -> NormalizedSKU:
    """Merge one inventory item with sales data into a NormalizedSKU."""
    avg_sales = compute_avg_daily_sales(orders, item.sku)

    # Special case: zero stock is always CRITICAL
    if item.current_stock <= 0:
        return NormalizedSKU(
            sku=item.sku,
            product_name=item.product_name,
            current_stock=item.current_stock,
            avg_daily_sales=avg_sales,
            days_of_supply=0.0,
            lead_time_days=config.DEFAULT_LEAD_TIME_DAYS,
            reorder_point=compute_reorder_point(avg_sales),
            suggested_reorder_qty=compute_suggested_reorder_qty(avg_sales),
            urgency="CRITICAL",
        )

    dos = compute_days_of_supply(item.current_stock, avg_sales)

    return NormalizedSKU(
        sku=item.sku,
        product_name=item.product_name,
        current_stock=item.current_stock,
        avg_daily_sales=round(avg_sales, 2),
        days_of_supply=round(dos, 2) if dos != inf else inf,
        lead_time_days=config.DEFAULT_LEAD_TIME_DAYS,
        reorder_point=round(compute_reorder_point(avg_sales), 1),
        suggested_reorder_qty=compute_suggested_reorder_qty(avg_sales),
        urgency=classify_urgency(dos),
    )


def normalize_all(
    inventory: list[RawInventoryItem],
    orders: list[RawOrderLine],
) -> list[NormalizedSKU]:
    """Normalize every inventory item."""
    return [normalize_sku(item, orders) for item in inventory]


def filter_alertable(skus: list[NormalizedSKU]) -> list[NormalizedSKU]:
    """Keep only SKUs that need attention (not HEALTHY)."""
    return [s for s in skus if s.urgency != "HEALTHY"]