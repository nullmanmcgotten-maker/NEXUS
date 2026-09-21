from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from .live_models import OrderRecord, utc_now


class TradeJournal:
    def __init__(self, path: str = "data/nexus_trades.sqlite3"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS orders (client_order_id TEXT PRIMARY KEY, symbol TEXT, side TEXT, order_type TEXT, quantity REAL, state TEXT, exchange_order_id TEXT, entry_price REAL, stop_order_id TEXT, target_order_id TEXT, updated_at TEXT, raw_json TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS analyses (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, setup TEXT, approved INTEGER, grade TEXT, confidence REAL, expected_net_r REAL, created_at TEXT, payload TEXT)")
        self.db.commit()

    def record(self, order: OrderRecord) -> None:
        self.db.execute("INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (order.client_order_id, order.symbol, order.side, order.order_type, order.quantity, order.state, order.exchange_order_id, order.entry_price, order.stop_order_id, order.target_order_id, order.updated_at, json.dumps(order.raw)))
        self.db.commit()

    def record_analysis(self, decision: Any) -> None:
        self.db.execute("INSERT INTO analyses(symbol,setup,approved,grade,confidence,expected_net_r,created_at,payload) VALUES (?,?,?,?,?,?,?,?)", (decision.feature_snapshot.get("symbol", ""), decision.setup, int(decision.approved), decision.grade, decision.confidence, decision.expected_net_r, utc_now(), json.dumps(decision.feature_snapshot, default=str)))
        self.db.commit()

    def record_gate(self, symbol: str, gate: str, payload: Any) -> None:
        self.db.execute("INSERT INTO analyses(symbol,setup,approved,grade,confidence,expected_net_r,created_at,payload) VALUES (?,?,?,?,?,?,?,?)", (symbol, f"GATE:{gate}", 0, "BLOCK", 0, 0, utc_now(), json.dumps(payload, default=str)))
        self.db.commit()

    def setup_stats(self, setup: str) -> dict[str, int]:
        # Outcome columns can be added by the fill/outcome reconciler; until then no calibration bias is applied.
        row = self.db.execute("SELECT COUNT(*) FROM analyses WHERE setup=?", (setup,)).fetchone()
        return {"count": int(row[0] if row else 0), "wins": 0}

    def get(self, client_order_id: str) -> Optional[tuple]:
        return self.db.execute("SELECT * FROM orders WHERE client_order_id=?", (client_order_id,)).fetchone()
