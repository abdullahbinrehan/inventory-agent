"""
Analysis engine.

Takes raw inventory + order lines and produces NormalizedSKU objects with
computed metrics and an urgency tier. Pure Python, no LLM.
"""

from datetime import datetime, timedelta, timezone
from math import inf

from agent import config
from agent.models import RawInventoryItem, RawOrderLine, NormalizedSKU


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_iso(ts: str) -> datetime:
    """Parse an ISO timestamp into an aware datetime (UTC if naive)."""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------

def compute_avg_daily_sales(
    orders: list[RawOrderLine],
    sku: str,
    window_days: int = config.SALES_WINDOW_DAYS,
) -> float:
    """Sum quantities sold for a SKU within the last `window_days`, / window_days."""
    if window_days <= 0:
        return 0.0

    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    total_qty = 0
    for o in orders:
        if o.sku != sku:
            continue
        try:
            order_dt = _parse_iso(o.created_at)
        except (ValueError, TypeError):
            continue
        if order_dt < cutoff:
            continue
        total_qty += o.quantity
    return total_qty / window_days


def compute_sales_trend_pct(
    orders: list[RawOrderLine],
    sku: str,
    window_days: int = config.SALES_WINDOW_DAYS,
) -> float:
    """
    Compare this week's sales to last week's.
    Returns percent change as a float (0.42 = +42%, -0.30 = -30%).
    Returns 0.0 if there's no prior-week baseline.
    """
    now = datetime.now(timezone.utc)
    this_week_start = now - timedelta(days=window_days)
    last_week_start = now - timedelta(days=window_days * 2)

    this_week = 0
    last_week = 0

    for o in orders:
        if o.sku != sku:
            continue
        try:
            order_dt = _parse_iso(o.created_at)
        except (ValueError, TypeError):
            continue
        if order_dt >= this_week_start:
            this_week += o.quantity
        elif order_dt >= last_week_start:
            last_week += o.quantity

    if last_week == 0:
        return 0.0
    return round((this_week - last_week) / last_week, 2)


def compute_spike_ratio(
    orders: list[RawOrderLine],
    sku: str,
    avg_daily_sales: float,
) -> float:
    """
    Today's sales / avg daily sales. 1.0 = normal, 3.0 = 3x spike.
    Returns 1.0 if there's no baseline or no sales today.
    """
    if avg_daily_sales <= 0:
        return 1.0

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    today_qty = 0
    for o in orders:
        if o.sku != sku:
            continue
        try:
            order_dt = _parse_iso(o.created_at)
        except (ValueError, TypeError):
            continue
        if order_dt >= today_start:
            today_qty += o.quantity

    if today_qty == 0:
        return 1.0
    return round(today_qty / avg_daily_sales, 2)


def compute_days_of_supply(current_stock: int, avg_daily_sales: float) -> float:
    """Days until stockout at current rate. Returns inf if sales are zero."""
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
    trend = compute_sales_trend_pct(orders, item.sku)
    spike = compute_spike_ratio(orders, item.sku, avg_sales)

    # Special case: zero stock is always CRITICAL
    if item.current_stock <= 0:
        return NormalizedSKU(
            sku=item.sku,
            product_name=item.product_name,
            current_stock=item.current_stock,
            avg_daily_sales=round(avg_sales, 2),
            days_of_supply=0.0,
            lead_time_days=config.DEFAULT_LEAD_TIME_DAYS,
            reorder_point=compute_reorder_point(avg_sales),
            suggested_reorder_qty=compute_suggested_reorder_qty(avg_sales),
            urgency="CRITICAL",
            sales_trend_pct=trend,
            spike_ratio=spike,
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
        sales_trend_pct=trend,
        spike_ratio=spike,
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