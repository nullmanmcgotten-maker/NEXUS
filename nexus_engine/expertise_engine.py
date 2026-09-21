from __future__ import annotations

from datetime import datetime, timezone

from .data_quality import DataQualityGate
from .indicators import calculate_features
from .liquidity import map_liquidity
from .market_math import normalize_klines
from .orderflow_quality import analyze_flow_persistence
from .setup_detectors import classify_regime, setup_detectors
from .thesis_engine import ConfidenceCalibrator, build_decision
from .expertise import aggregate_order_flow, analyze_perpetual
from .structure import analyze_structure


class PerpetualExpertiseEngine:
    INTERVALS = ("12h", "8h", "4h", "2h", "1h", "15m", "5m")

    def __init__(self, adapter, journal, max_signal_age_seconds: int = 90):
        self.adapter = adapter; self.journal = journal; self.quality = DataQualityGate(); self.max_signal_age_seconds = max_signal_age_seconds

    def analyze(self, symbol: str):
        raw = {f"{tf}_candles": self.adapter.fetch_klines(tf, 200, symbol) for tf in self.INTERVALS}
        raw.update({"trades": self.adapter.fetch_aggregate_trades(symbol), "mark": self.adapter.fetch_mark_price(symbol), "oi": self.adapter.fetch_open_interest(symbol)})
        quality = self.quality.check(raw)
        if not quality.ok:
            raise RuntimeError("signal_data_blocked:" + ",".join(quality.reasons))
        candles = {tf: normalize_klines(raw[f"{tf}_candles"]) for tf in self.INTERVALS}
        features = {tf: calculate_features(tf, c) for tf, c in candles.items()}
        structure = analyze_structure(features, candles)
        flow = aggregate_order_flow(raw["trades"])
        flow_quality = analyze_flow_persistence([flow.imbalance], [0.0])
        mark = raw["mark"]; oi_now = float(raw["oi"].get("openInterest", 0))
        perp = analyze_perpetual(mark, oi_now, oi_now, [])
        liquidity = map_liquidity(candles["15m"], features["5m"].close)
        regime = classify_regime({"bias": structure.bias, "alignment": structure.alignment, "state": structure.state}, features["15m"].volatility, {"liquidation_event": False})
        candidates = setup_detectors({"bias": structure.bias, "alignment": structure.alignment, "state": structure.state}, liquidity.__dict__, {"rolling_imbalance": flow_quality.rolling_imbalance}, perp.__dict__, regime)
        if not candidates:
            return build_decision({"setup": "NONE", "side": "NONE", "score": 0, "reasons": ["no_setup"]}, features["5m"].close, features["5m"].close, features["5m"].close, regime, {"quality": quality.__dict__}, ConfidenceCalibrator(self.journal), self.max_signal_age_seconds)
        candidate = max(candidates, key=lambda x: x["score"])
        price = features["5m"].close; risk = max(features["5m"].atr, price * .001)
        stop = price - risk if candidate["side"] == "BUY" else price + risk
        target = price + risk * 1.8 if candidate["side"] == "BUY" else price - risk * 1.8
        snapshot = {"symbol": symbol, "quality": quality.__dict__, "structure": structure.__dict__, "features": {k: v.__dict__ for k, v in features.items()}, "flow": flow.__dict__, "flow_quality": flow_quality.__dict__, "perp": perp.__dict__, "liquidity": liquidity.__dict__, "regime": regime}
        return build_decision(candidate, price, stop, target, regime, snapshot, ConfidenceCalibrator(self.journal), self.max_signal_age_seconds)
