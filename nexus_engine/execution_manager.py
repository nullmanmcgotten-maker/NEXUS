from __future__ import annotations

from typing import Dict, Optional

from nexus_engine.config import Settings
from nexus_engine.live.binance_futures import BinanceFuturesAdapter


class ExecutionManager:
    """Live execution manager with approval gates before order submission."""

    def __init__(self, settings: Settings, adapter: BinanceFuturesAdapter):
        self.settings = settings
        self.adapter = adapter

    def should_submit(self, trade_signal: Dict[str, object]) -> bool:
        if not self.settings.enable_live_orders:
            return False
        if not self.settings.binance_api_key or not self.settings.binance_api_secret:
            return False
        if not trade_signal.get("approved"):
            return False
        return True

    def submit_order(self, side: str, quantity: float, price: Optional[float] = None) -> Dict[str, object]:
        if not self.should_submit({"approved": True}):
            raise RuntimeError("Live order submission is disabled or missing exchange credentials.")

        response = self.adapter.create_order(
            side=side,
            quantity=quantity,
            order_type="MARKET",
            symbol=self.settings.symbol,
            price=price,
        )
        return response
