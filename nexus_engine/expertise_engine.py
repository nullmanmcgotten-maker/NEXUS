from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .data_quality import DataQualityGate
from .expertise import aggregate_order_flow, analyze_perpetual
from .indicators import calculate_features
from .liquidity import map_liquidity
from .market_math import normalize_klines
from .orderflow_quality import analyze_flow_persistence
from .setup_detectors import classify_regime, setup_detectors
from .structure import analyze_structure
from .thesis_engine import ConfidenceCalibrator, build_decision


class PerpetualExpertiseEngine:
    INTERVALS = ("12h", "8h", "4h", "2h", "1h", "15m", "5m")

    def __init__(self, adapter: Any, journal: Any, max_signal_age_seconds: int = 90):
        self.adapter = adapter
        self.journal = journal
        self.quality = DataQualityGate()
        self.max_signal_age_seconds = max_signal_age_seconds

    def analyze(self, symbol: str):
        raw = {f"{tf}_candles": self.adapter.fetch_klines(tf, 200, symbol) for tf in self.INTERVALS}
        raw.update({
            "trades": self.adapter.fetch_aggregate_trades(symbol),
            "mark": self.adapter.fetch_mark_price(symbol),
            "oi": self.adapter.fetch_open_interest(symbol),
            "oi_history": self.adapter.fetch_open_interest_history(symbol),
            "liquidations": self.adapter.fetch_force_orders(symbol),
            "exchange_info": self.adapter.fetch_exchange_info(),
        })
        quality = self.quality.check(raw)
        if not quality["ok"]:
            decision = build_decision(
                {"setup": "NONE", "side": "NONE", "score": 0, "reasons": list(quality["reasons"])},
                0.0, 0.0, 0.0, "NO_TRADE", {"symbol": symbol, "quality": quality},
                ConfidenceCalibrator(self.journal), self.max_signal_age_seconds,
            )
            self.journal.record_analysis(decision)
            return decision

        candles = {tf: normalize_klines(raw[f"{tf}_candles"]) for tf in self.INTERVALS}
        features = {tf: calculate_features(tf, data) for tf, data in candles.items()}
        structure = analyze_structure(features, candles)
        flow = aggregate_order_flow(raw["trades"])
        flow_quality = analyze_flow_persistence([flow.imbalance], [0.0])
        oi_history = raw["oi_history"]
        previous_oi = float(oi_history[-2].get("sumOpenInterest", 0)) if len(oi_history) >= 2 else float(raw["oi"].get("openInterest", 0))
        perp = analyze_perpetual(raw["mark"], float(raw["oi"].get("openInterest", 0)), previous_oi, raw["liquidations"])
        liquidity = map_liquidity(candles["15m"], features["5m"].close)
        regime = classify_regime({"bias": structure.bias, "alignment": structure.alignment, "state": structure.state}, features["15m"].volatility, {"liquidation_event": bool(raw["liquidations"])})
        candidates = setup_detectors(
            {"bias": structure.bias, "alignment": structure.alignment, "state": structure.state},
            liquidity.__dict__, {"rolling_imbalance": flow_quality.rolling_imbalance}, perp.__dict__, regime,
        )
        snapshot = {
            "symbol": symbol, "quality": quality, "structure": structure.__dict__,
            "features": {key: value.__dict__ for key, value in features.items()},
            "flow": flow.__dict__, "flow_quality": flow_quality.__dict__,
            "perpetual": perp.__dict__, "liquidity": liquidity.__dict__, "regime": regime,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        if not candidates:
            decision = build_decision({"setup": "NONE", "side": "NONE", "score": 0, "reasons": ["no_valid_setup"]}, features["5m"].close, features["5m"].close, features["5m"].close, regime, snapshot, ConfidenceCalibrator(self.journal), self.max_signal_age_seconds)
        else:
            candidate = max(candidates, key=lambda item: item["score"])
            price = features["5m"].close
            risk = max(features["5m"].atr, price * 0.001)
            stop = price - risk if candidate["side"] == "BUY" else price + risk
            target = price + risk * 1.8 if candidate["side"] == "BUY" else price - risk * 1.8
            decision = build_decision(candidate, price, stop, target, regime, snapshot, ConfidenceCalibrator(self.journal), self.max_signal_age_seconds)
        self.journal.record_analysis(decision)
        return decision
