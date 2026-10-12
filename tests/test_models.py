from agent.models import (
    RawInventoryItem,
    RawOrderLine,
    NormalizedSKU,
    AlertRecord,
    Alert,
)


def test_raw_inventory_item():
    item = RawInventoryItem(sku="TSHIRT-BLK-M", product_name="Black Tee M", current_stock=8)
    assert item.sku == "TSHIRT-BLK-M"
    assert item.current_stock == 8
    assert item.location_id is None


def test_raw_order_line():
    line = RawOrderLine(
        order_id="1001",
        created_at="2026-10-08T14:22:00Z",
        sku="TSHIRT-BLK-M",
        quantity=2,
        price=19.99,
    )
    assert line.quantity == 2
    assert line.price == 19.99


def test_normalized_sku():
    n = NormalizedSKU(
        sku="TSHIRT-BLK-M",
        product_name="Black Tee M",
        current_stock=8,
        avg_daily_sales=2.7,
        days_of_supply=2.96,
        lead_time_days=7,
        reorder_point=22.0,
        suggested_reorder_qty=26,
        urgency="CRITICAL",
    )
    assert n.urgency == "CRITICAL"
    assert n.suggested_reorder_qty == 26


def test_alert_record():
    rec = AlertRecord(
        sku="TSHIRT-BLK-M",
        last_alerted_at="2026-10-09T08:00:00Z",
        urgency="CRITICAL",
    )
    assert rec.alert_count_7d == 1


def test_alert():
    a = Alert(title="Low Stock", body="Body text", urgency="CRITICAL", skus=["SKU1"])
    assert a.title == "Low Stock"
    assert a.skus == ["SKU1"]
    assert a.created_at.endswith("Z")