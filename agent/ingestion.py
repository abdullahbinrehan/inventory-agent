"""
Ingestion layer.

Reads raw data from a source (mock files now, Shopify later) and returns
RawInventoryItem and RawOrderLine objects. Everything downstream talks to
this layer, never to files or APIs directly.
"""

import json
from datetime import datetime, timedelta
from typing import Optional

from agent import config
from agent.models import RawInventoryItem, RawOrderLine


# ---------------------------------------------------------------------------
# Mock data loaders
# ---------------------------------------------------------------------------

def load_mock_inventory() -> list[RawInventoryItem]:
    """Read data/mock_inventory.json and return RawInventoryItem objects."""
    with open(config.MOCK_INVENTORY_FILE, "r") as f:
        raw = json.load(f)

    items = []
    for row in raw:
        items.append(
            RawInventoryItem(
                sku=row["sku"],
                product_name=row["product_name"],
                current_stock=row["current_stock"],
                location_id=row.get("location_id"),
                updated_at=row.get("updated_at"),
            )
        )
    return items


def load_mock_orders() -> list[RawOrderLine]:
    """
    Read data/mock_orders.json and flatten each order's line_items into
    individual RawOrderLine objects.
    """
    with open(config.MOCK_ORDERS_FILE, "r") as f:
        raw = json.load(f)

    lines = []
    for order in raw:
        for item in order["line_items"]:
            lines.append(
                RawOrderLine(
                    order_id=order["order_id"],
                    created_at=order["created_at"],
                    sku=item["sku"],
                    quantity=item["quantity"],
                    price=item.get("price", 0.0),
                )
            )
    return lines


# ---------------------------------------------------------------------------
# Shopify loaders (stubs — implemented in Phase 9)
# ---------------------------------------------------------------------------

def fetch_shopify_inventory() -> list[RawInventoryItem]:
    """Fetch live inventory from Shopify Admin API. Not implemented yet."""
    raise NotImplementedError("Shopify ingestion is implemented in Phase 9")


def fetch_shopify_orders(days: int = config.SALES_WINDOW_DAYS) -> list[RawOrderLine]:
    """Fetch recent orders from Shopify Admin API. Not implemented yet."""
    raise NotImplementedError("Shopify ingestion is implemented in Phase 9")


# ---------------------------------------------------------------------------
# Dispatchers — the only functions the rest of the pipeline calls
# ---------------------------------------------------------------------------

def get_inventory(source: str = "mock") -> list[RawInventoryItem]:
    """Return inventory items from the requested source."""
    if source == "mock":
        return load_mock_inventory()
    if source == "shopify":
        return fetch_shopify_inventory()
    raise ValueError(f"Unknown source: {source}")


def get_orders(
    source: str = "mock",
    days: int = config.SALES_WINDOW_DAYS,
) -> list[RawOrderLine]:
    """Return recent order lines from the requested source."""
    if source == "mock":
        return load_mock_orders()
    if source == "shopify":
        return fetch_shopify_orders(days=days)
    raise ValueError(f"Unknown source: {source}")