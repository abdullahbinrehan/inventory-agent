from math import inf

import pytest

from agent.analysis import (
    compute_avg_daily_sales,
    compute_days_of_supply,
    compute_reorder_point,
    compute_suggested_reorder_qty,
    classify_urgency,
    normalize_all,
    filter_alertable,
)
from agent.ingestion import get_inventory, get_orders
from agent.models import RawOrderLine


# ---------------------------------------------------------------------------
# Unit tests for individual functions
# ---------------------------------------------------------------------------

def test_avg_daily_sales_basic():
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)

    def recent(days):
        return (now - timedelta(days=days)).isoformat().replace("+00:00", "Z")

    orders = [
        RawOrderLine("1", recent(1), "SKU-A", 5, 1.0),
        RawOrderLine("2", recent(2), "SKU-A", 9, 1.0),
        RawOrderLine("3", recent(3), "SKU-B", 100, 1.0),
    ]
    assert compute_avg_daily_sales(orders, "SKU-A", window_days=7) == 2.0
    assert compute_avg_daily_sales(orders, "SKU-B", window_days=7) == 100 / 7


def test_days_of_supply_normal():
    assert compute_days_of_supply(10, 2.0) == 5.0


def test_days_of_supply_zero_sales_returns_inf():
    assert compute_days_of_supply(100, 0) == inf


def test_reorder_point():
    # 2/day * 7 days * 1.5 = 21
    assert compute_reorder_point(2.0, lead_time_days=7, safety_factor=1.5) == 21.0


def test_suggested_reorder_qty_rounds():
    # 2.7 * 7 * 1.5 = 28.35 -> 28
    assert compute_suggested_reorder_qty(2.7, lead_time_days=7, safety_factor=1.5) == 28


def test_classify_urgency_all_tiers():
    assert classify_urgency(0.5) == "CRITICAL"
    assert classify_urgency(2.9) == "CRITICAL"
    assert classify_urgency(3.0) == "HIGH"
    assert classify_urgency(6.9) == "HIGH"
    assert classify_urgency(7.0) == "NORMAL"
    assert classify_urgency(13.9) == "NORMAL"
    assert classify_urgency(14.0) == "HEALTHY"
    assert classify_urgency(inf) == "HEALTHY"


# ---------------------------------------------------------------------------
# Integration tests against mock data
# ---------------------------------------------------------------------------

def test_normalize_all_produces_ten_skus():
    skus = normalize_all(get_inventory("mock"), get_orders("mock"))
    assert len(skus) == 10


def test_filter_alertable_excludes_healthy():
    skus = normalize_all(get_inventory("mock"), get_orders("mock"))
    alertable = filter_alertable(skus)

    # No HEALTHY items in the filtered list
    assert all(s.urgency != "HEALTHY" for s in alertable)

    # Should have a reasonable number of alertable SKUs
    assert len(alertable) >= 5

    # These must always be critical based on mock setup
    critical_skus = {s.sku for s in alertable if s.urgency == "CRITICAL"}
    assert "TSHIRT-BLK-M" in critical_skus
    assert "TSHIRT-WHT-L" in critical_skus
    assert "LIMITED-HAT" in critical_skus


def test_limited_hat_is_critical():
    skus = normalize_all(get_inventory("mock"), get_orders("mock"))
    hat = next(s for s in skus if s.sku == "LIMITED-HAT")
    assert hat.urgency == "CRITICAL"
    assert hat.current_stock == 0


def test_vintage_tee_is_healthy():
    """Zero sales → dead stock → not urgent."""
    skus = normalize_all(get_inventory("mock"), get_orders("mock"))
    tee = next(s for s in skus if s.sku == "VINTAGE-2019-TEE")
    assert tee.urgency == "HEALTHY"
    assert tee.days_of_supply == inf