"""
Generates mock inventory and orders for development.
Run: python scripts/generate_mock_data.py
"""

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# (sku, product_name, current_stock, avg_daily_sales)
SKUS = [
    ("TSHIRT-BLK-M",     "Black T-Shirt (Medium)",   8,   2.7),
    ("TSHIRT-WHT-L",     "White T-Shirt (Large)",    5,   2.0),
    ("MUG-CERAMIC",      "Ceramic Mug",              20,  3.0),
    ("HOODIE-GRY-XL",    "Grey Hoodie (XL)",         15,  2.3),
    ("CAP-BLK-OS",       "Black Cap (One Size)",     30,  2.5),
    ("SOCKS-WHT-3PK",    "White Socks (3-Pack)",     40,  3.0),
    ("STICKER-PACK",     "Sticker Pack",             500, 2.0),
    ("POSTER-A2",        "A2 Poster",                100, 1.0),
    ("VINTAGE-2019-TEE", "Vintage 2019 Tee",         50,  0.0),
    ("LIMITED-HAT",      "Limited Edition Hat",      0,   1.0),
]

PRICE = {
    "TSHIRT-BLK-M": 19.99,
    "TSHIRT-WHT-L": 19.99,
    "MUG-CERAMIC": 12.50,
    "HOODIE-GRY-XL": 49.99,
    "CAP-BLK-OS": 24.99,
    "SOCKS-WHT-3PK": 9.99,
    "STICKER-PACK": 4.99,
    "POSTER-A2": 14.99,
    "VINTAGE-2019-TEE": 15.00,
    "LIMITED-HAT": 34.99,
}

random.seed(42)  # Reproducible output

now_utc = datetime.now(timezone.utc)

# --- Build inventory JSON ---
inventory = []
for sku, name, stock, _ in SKUS:
    inventory.append({
        "sku": sku,
        "product_name": name,
        "current_stock": stock,
        "location_id": "gid://shopify/Location/1",
        "updated_at": now_utc.isoformat().replace("+00:00", "Z"),
    })

with open(DATA_DIR / "mock_inventory.json", "w") as f:
    json.dump(inventory, f, indent=2)

# --- Build orders JSON (last 30 days) ---
orders = []
order_id = 1000

for day_offset in range(30):
    day = now_utc - timedelta(days=day_offset)
    for sku, _, _, avg in SKUS:
        if avg <= 0:
            continue
        qty = max(0, round(avg + random.uniform(-1.0, 1.0)))
        if qty == 0:
            continue
        order_id += 1
        orders.append({
            "order_id": str(order_id),
            "created_at": day.replace(
                hour=random.randint(8, 20),
                minute=random.randint(0, 59),
            ).isoformat().replace("+00:00", "Z"),
            "line_items": [
                {
                    "sku": sku,
                    "quantity": qty,
                    "price": PRICE.get(sku, 0.0),
                }
            ],
        })

with open(DATA_DIR / "mock_orders.json", "w") as f:
    json.dump(orders, f, indent=2)

print(f"Wrote {len(inventory)} inventory items to mock_inventory.json")
print(f"Wrote {len(orders)} orders to mock_orders.json")