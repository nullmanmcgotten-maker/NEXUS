from __future__ import annotations

from typing import Any

from .market_math import normalize_klines
from .indicators import calculate_features
from .expertise import aggregate_order_flow, analyze_perpetual, build_thesis
from .structure import analyze_structure


class PerpetualExpertiseEngine:
    INTERVALS = ("12h", "8h", "4h", "2h", "1h", "15m", "5m")

    def __init__(self, adapter: Any):
        self.adapter = adapter

    def analyze(self, symbol: str) -> Any:
        candles_by_tf = {tf: normalize_klines(self.adapter.fetch_klines(tf, 200, symbol)) for tf in self.INTERVALS}
        features = {tf: calculate_features(tf, candles) for tf, candles in candles_by_tf.items() if candles}
        structure = analyze_structure(features, candles_by_tf)
        flow = aggregate_order_flow(self.adapter.fetch_aggregate_trades(symbol, 1000))
        mark = self.adapter.fetch_mark_price(symbol)
        oi = self.adapter.fetch_open_interest(symbol)
        oi_previous = self.adapter.fetch_open_interest_history(symbol, "5m", 2)
        previous = float(oi_previous[0].get("sumOpenInterest", 0)) if oi_previous else 0.0
        liquidations = self.adapter.fetch_force_orders(symbol, 100)
        perp = analyze_perpetual(mark, float(oi.get("openInterest", 0)), previous, liquidations)
        return build_thesis(symbol, features["5m"].close, structure, features, flow, perp)
