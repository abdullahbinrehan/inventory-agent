"""
Ingestion layer.
Reads raw data from a source (mock files or Shopify) and returns
RawInventoryItem and RawOrderLine objects.
"""

import json
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import requests

from agent import config
from agent.models import RawInventoryItem, RawOrderLine

API_VERSION = "2026-10"
_ACCESS_TOKEN: str | None = None


def load_mock_inventory() -> list[RawInventoryItem]:
    with open(config.MOCK_INVENTORY_FILE, "r") as f:
        raw = json.load(f)
    return [RawInventoryItem(sku=r["sku"], product_name=r["product_name"], current_stock=r["current_stock"], location_id=r.get("location_id"), updated_at=r.get("updated_at")) for r in raw]


def load_mock_orders() -> list[RawOrderLine]:
    with open(config.MOCK_ORDERS_FILE, "r") as f:
        raw = json.load(f)
    lines = []
    for order in raw:
        for item in order["line_items"]:
            lines.append(RawOrderLine(order_id=order["order_id"], created_at=order["created_at"], sku=item["sku"], quantity=item["quantity"], price=item.get("price", 0.0)))
    return lines


def _get_shopify_access_token(user_config: dict) -> str:
    url = f"https://{user_config['shopify_url']}/admin/oauth/access_token"
    payload = {
        "client_id": user_config['shopify_client_id'],
        "client_secret": user_config['shopify_client_secret'],
        "grant_type": "client_credentials",
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def _shopify_get(path: str, user_config: dict, params: dict | None = None) -> requests.Response:
    global _ACCESS_TOKEN
    if _ACCESS_TOKEN is None:
        _ACCESS_TOKEN = _get_shopify_access_token(user_config)

    url = f"https://{user_config['shopify_url']}/admin/api/{API_VERSION}/{path}"
    headers = {"X-Shopify-Access-Token": _ACCESS_TOKEN, "Content-Type": "application/json"}
    resp = requests.get(url, headers=headers, params=params, timeout=30)

    if resp.status_code == 429:
        time.sleep(int(resp.headers.get("Retry-After", 2)))
        resp = requests.get(url, headers=headers, params=params, timeout=30)

    resp.raise_for_status()
    return resp


def _paginate_shopify(path: str, key: str, user_config: dict, params: dict | None = None) -> list[dict]:
    results, current_params = [], dict(params or {})
    while True:
        resp = _shopify_get(path, user_config, current_params)
        results.extend(resp.json().get(key, []))
        link_header = resp.headers.get("Link", "")
        next_url = next((part.split(";")[0].strip().strip("<>") for part in link_header.split(",") if 'rel="next"' in part), None)
        if not next_url: break
        page_info = parse_qs(urlparse(next_url).query).get("page_info", [None])[0]
        if not page_info: break
        current_params = {"limit": 250, "page_info": page_info}
    return results


def fetch_shopify_inventory(user_config: dict) -> list[RawInventoryItem]:
    products = _paginate_shopify("products.json", "products", user_config, {"limit": 250, "fields": "id,title,variants"})
    sku_to_name, variant_to_sku = {}, {}
    for p in products:
        for v in p.get("variants", []):
            if v.get("sku"):
                sku_to_name[v["sku"]] = p.get("title", v["sku"])
                variant_to_sku[v["inventory_item_id"]] = v["sku"]

    locations = _paginate_shopify("locations.json", "locations", user_config, {"limit": 250})
    location_ids = [str(loc["id"]) for loc in locations]
    if not location_ids: return []

    levels = _paginate_shopify("inventory_levels.json", "inventory_levels", user_config, {"limit": 250, "location_ids": ",".join(location_ids)})
    
    stock_by_sku = {}
    for level in levels:
        sku = variant_to_sku.get(level.get("inventory_item_id"))
        if sku and level.get("available") is not None:
            stock_by_sku[sku] = stock_by_sku.get(sku, 0) + level["available"]

    return [RawInventoryItem(sku=s, product_name=sku_to_name.get(s, s), current_stock=stock, updated_at=None) for s, stock in stock_by_sku.items()]


def fetch_shopify_orders(user_config: dict, days: int = config.SALES_WINDOW_DAYS) -> list[RawOrderLine]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    orders = _paginate_shopify("orders.json", "orders", user_config, {"limit": 250, "status": "any", "created_at_min": since, "fields": "id,created_at,line_items"})
    
    lines = []
    for o in orders:
        for item in o.get("line_items", []):
            if item.get("sku"):
                lines.append(RawOrderLine(order_id=str(o["id"]), created_at=o["created_at"], sku=item["sku"], quantity=item.get("quantity", 0), price=float(item.get("price", 0.0))))
    return lines


def get_inventory(source: str, user_config: dict) -> list[RawInventoryItem]:
    if source == "mock": return load_mock_inventory()
    if source == "shopify": return fetch_shopify_inventory(user_config)
    raise ValueError(f"Unknown source: {source}")


def get_orders(source: str, user_config: dict, days: int = config.SALES_WINDOW_DAYS) -> list[RawOrderLine]:
    if source == "mock": return load_mock_orders()
    if source == "shopify": return fetch_shopify_orders(user_config, days)
    raise ValueError(f"Unknown source: {source}")