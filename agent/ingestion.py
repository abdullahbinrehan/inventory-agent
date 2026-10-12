"""
Ingestion layer.

Reads raw data from a source (mock files or Shopify) and returns
RawInventoryItem and RawOrderLine objects. Everything downstream talks to
this layer, never to files or APIs directly.
"""

import json
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import requests

from agent import config
from agent.models import RawInventoryItem, RawOrderLine


# ===========================================================================
# Mock data loaders
# ===========================================================================

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


# ===========================================================================
# Shopify client credentials auth
# ===========================================================================

API_VERSION = "2026-10"

_ACCESS_TOKEN: str | None = None


def _get_shopify_access_token() -> str:
    """
    Exchange Client ID + Client Secret for a temporary access token.
    Token lasts ~24 hours. Called once per pipeline run.
    """
    url = f"https://{config.SHOPIFY_STORE_URL}/admin/oauth/access_token"
    payload = {
        "client_id": config.SHOPIFY_CLIENT_ID,
        "client_secret": config.SHOPIFY_CLIENT_SECRET,
        "grant_type": "client_credentials",
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def _shopify_get(path: str, params: dict | None = None) -> requests.Response:
    """
    Make an authenticated GET request to the Shopify Admin API.
    Retries once after Retry-After seconds if rate-limited (HTTP 429).
    """
    global _ACCESS_TOKEN
    if _ACCESS_TOKEN is None:
        _ACCESS_TOKEN = _get_shopify_access_token()

    url = f"https://{config.SHOPIFY_STORE_URL}/admin/api/{API_VERSION}/{path}"
    headers = {
        "X-Shopify-Access-Token": _ACCESS_TOKEN,
        "Content-Type": "application/json",
    }

    resp = requests.get(url, headers=headers, params=params, timeout=30)

    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 2))
        time.sleep(retry_after)
        resp = requests.get(url, headers=headers, params=params, timeout=30)

    resp.raise_for_status()
    return resp


def _paginate_shopify(path: str, key: str, params: dict | None = None) -> list[dict]:
    """
    Follow Shopify's Link header pagination and collect all items.
    `key` is the JSON key holding the list (e.g. "orders").
    """
    results: list[dict] = []
    current_params = dict(params or {})

    while True:
        resp = _shopify_get(path, current_params)
        data = resp.json()
        results.extend(data.get(key, []))

        link_header = resp.headers.get("Link", "")
        next_url = None
        for part in link_header.split(","):
            if 'rel="next"' in part:
                next_url = part.split(";")[0].strip().strip("<>")
                break

        if not next_url:
            break

        parsed = urlparse(next_url)
        page_info = parse_qs(parsed.query).get("page_info", [None])[0]
        if not page_info:
            break

        current_params = {"limit": 250, "page_info": page_info}

    return results


# ===========================================================================
# Shopify loaders
# ===========================================================================

def fetch_shopify_inventory() -> list[RawInventoryItem]:
    """
    1. Fetch all products to get SKU -> product_name mapping.
    2. Fetch all locations to get location IDs.
    3. Fetch inventory levels filtered by those location IDs.
    4. Aggregate stock per SKU (sum across locations).
    5. Skip untracked items (available is None).
    """
    # Step 1: products
    products = _paginate_shopify(
        "products.json",
        "products",
        {"limit": 250, "fields": "id,title,variants"},
    )

    sku_to_name: dict[str, str] = {}
    variant_to_sku: dict[int, str] = {}

    for p in products:
        for v in p.get("variants", []):
            sku = v.get("sku") or ""
            if not sku:
                continue
            sku_to_name[sku] = p.get("title", sku)
            variant_to_sku[v["inventory_item_id"]] = sku

    # Step 2: locations
    locations = _paginate_shopify(
        "locations.json",
        "locations",
        {"limit": 250},
    )
    location_ids = [str(loc["id"]) for loc in locations]

    if not location_ids:
        return []

    # Step 3: inventory levels
    levels = _paginate_shopify(
        "inventory_levels.json",
        "inventory_levels",
        {"limit": 250, "location_ids": ",".join(location_ids)},
    )

    # Step 4: aggregate per SKU
    stock_by_sku: dict[str, int] = {}
    updated_by_sku: dict[str, str] = {}

    for level in levels:
        item_id = level.get("inventory_item_id")
        sku = variant_to_sku.get(item_id)
        if not sku:
            continue

        # Skip untracked items (available is None)
        available = level.get("available")
        if available is None:
            continue

        stock_by_sku[sku] = stock_by_sku.get(sku, 0) + available
        if level.get("updated_at"):
            updated_by_sku[sku] = level["updated_at"]

    # Step 5: build final list (one entry per SKU)
    items: list[RawInventoryItem] = []
    for sku, total_stock in stock_by_sku.items():
        items.append(
            RawInventoryItem(
                sku=sku,
                product_name=sku_to_name.get(sku, sku),
                current_stock=total_stock,
                location_id=None,  # aggregated across all locations
                updated_at=updated_by_sku.get(sku),
            )
        )
    return items


def fetch_shopify_orders(days: int = config.SALES_WINDOW_DAYS) -> list[RawOrderLine]:
    """
    Fetch orders from the last `days` days and flatten line_items into
    individual RawOrderLine objects.
    """
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    orders = _paginate_shopify(
        "orders.json",
        "orders",
        {
            "limit": 250,
            "status": "any",
            "created_at_min": since,
            "fields": "id,created_at,line_items",
        },
    )

    lines: list[RawOrderLine] = []
    for order in orders:
        for item in order.get("line_items", []):
            sku = item.get("sku") or ""
            if not sku:
                continue
            lines.append(
                RawOrderLine(
                    order_id=str(order["id"]),
                    created_at=order["created_at"],
                    sku=sku,
                    quantity=item.get("quantity", 0),
                    price=float(item.get("price", 0.0)),
                )
            )
    return lines


# ===========================================================================
# Dispatchers — the only functions the rest of the pipeline calls
# ===========================================================================

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