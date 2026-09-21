from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from typing import Any, Optional

from .live_models import OrderRecord, utc_now


class TradeJournal:
    def __init__(self, path: str = "data/nexus_trades.sqlite3"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("""CREATE TABLE IF NOT EXISTS orders (
            client_order_id TEXT PRIMARY KEY, symbol TEXT, side TEXT, order_type TEXT,
            quantity REAL, state TEXT, exchange_order_id TEXT, entry_price REAL,
            stop_order_id TEXT, target_order_id TEXT, updated_at TEXT, raw_json TEXT)""")
        self.db.commit()

    def record(self, order: OrderRecord) -> None:
        self.db.execute("""INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
            order.client_order_id, order.symbol, order.side, order.order_type,
            order.quantity, order.state, order.exchange_order_id, order.entry_price,
            order.stop_order_id, order.target_order_id, order.updated_at, json.dumps(order.raw),
        ))
        self.db.commit()

    def update_from_exchange(self, client_order_id: str, raw: dict[str, Any]) -> None:
        state = str(raw.get("status", "UNKNOWN")).upper()
        mapping = {"NEW":"SUBMITTED", "PARTIALLY_FILLED":"PARTIALLY_FILLED", "FILLED":"FILLED", "CANCELED":"CANCELED", "REJECTED":"REJECTED", "EXPIRED":"CANCELED"}
        self.db.execute("UPDATE orders SET state=?, exchange_order_id=?, entry_price=?, updated_at=?, raw_json=? WHERE client_order_id=?",
                        (mapping.get(state, "UNKNOWN"), str(raw.get("orderId")) if raw.get("orderId") else None,
                         float(raw.get("avgPrice", 0) or 0), utc_now(), json.dumps(raw), client_order_id))
        self.db.commit()

    def get(self, client_order_id: str) -> Optional[tuple]:
        return self.db.execute("SELECT * FROM orders WHERE client_order_id=?", (client_order_id,)).fetchone()
