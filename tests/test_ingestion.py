from agent.ingestion import get_inventory, get_orders
from agent.models import RawInventoryItem, RawOrderLine


def test_get_mock_inventory_returns_items():
    items = get_inventory("mock")
    assert len(items) == 10
    assert all(isinstance(i, RawInventoryItem) for i in items)


def test_mock_inventory_has_expected_sku():
    items = get_inventory("mock")
    skus = {i.sku for i in items}
    assert "TSHIRT-BLK-M" in skus
    assert "LIMITED-HAT" in skus


def test_get_mock_orders_returns_lines():
    lines = get_orders("mock")
    assert len(lines) > 100
    assert all(isinstance(l, RawOrderLine) for l in lines)


def test_mock_orders_have_positive_quantity():
    lines = get_orders("mock")
    assert all(l.quantity > 0 for l in lines)


def test_unknown_source_raises():
    import pytest
    with pytest.raises(ValueError):
        get_inventory("nonsense")
    with pytest.raises(ValueError):
        get_orders("nonsense")