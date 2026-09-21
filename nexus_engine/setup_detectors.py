from __future__ import annotations

from .signal_models import SignalDecision


def classify_regime(structure: dict, volatility: float, flow: dict) -> str:
    if flow.get("liquidation_event"):
        return "LIQUIDATION_EVENT"
    if structure.get("alignment", 0) >= 0.75 and structure.get("bias") == "bullish":
        return "TREND_UP"
    if structure.get("alignment", 0) >= 0.75 and structure.get("bias") == "bearish":
        return "TREND_DOWN"
    if volatility < 0.01:
        return "COMPRESSION"
    if structure.get("state") == "range":
        return "RANGE"
    return "TRANSITION"


def setup_detectors(structure: dict, liquidity: dict, flow: dict, perp: dict, regime: str) -> list[dict]:
    candidates = []
    imbalance = float(flow.get("rolling_imbalance", 0))
    if regime in {"TREND_UP", "COMPRESSION"} and structure.get("bias") == "bullish" and imbalance > 0.12 and liquidity.get("room_for_long"):
        candidates.append({"setup": "PRE_PUMP_ABSORPTION", "side": "BUY", "score": .82, "reasons": ["macro_alignment", "persistent_buy_flow", "room_to_resistance"]})
    if regime in {"TREND_DOWN", "LIQUIDATION_EVENT"} and structure.get("bias") == "bearish" and imbalance < -0.12 and perp.get("crowding") == "long_crowded":
        candidates.append({"setup": "EXHAUSTION_REVERSAL", "side": "SELL", "score": .80, "reasons": ["bearish_structure", "persistent_sell_flow", "long_crowding"]})
    if regime == "COMPRESSION" and abs(imbalance) > .18:
        candidates.append({"setup": "BREAKOUT_ACCEPTANCE", "side": "BUY" if imbalance > 0 else "SELL", "score": .76, "reasons": ["compression", "flow_expansion"]})
    if regime == "RANGE" and abs(imbalance) > .22 and liquidity.get("swept_side"):
        candidates.append({"setup": "FAILED_BREAKOUT", "side": "SELL" if liquidity["swept_side"] == "buy_side" else "BUY", "score": .74, "reasons": ["liquidity_sweep", "range_rejection"]})
    if regime in {"TREND_UP", "TREND_DOWN"} and abs(imbalance) > .10:
        candidates.append({"setup": "TREND_PULLBACK", "side": "BUY" if regime == "TREND_UP" else "SELL", "score": .72, "reasons": ["trend_regime", "flow_return"]})
    return candidates
