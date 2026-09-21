from __future__ import annotations

from .signal_models import LiquidityMap


def map_liquidity(candles: list, current: float, lookback: int = 60) -> LiquidityMap:
    recent = candles[-lookback:]
    if not recent:
        return LiquidityMap(0, 0, 0, 0, False, False)
    support = min(float(c.low) for c in recent)
    resistance = max(float(c.high) for c in recent)
    support_distance = (current - support) / current if current else 0
    resistance_distance = (resistance - current) / current if current else 0
    swept = None
    if len(recent) >= 2:
        previous = recent[-2]
        latest = recent[-1]
        if latest.low < previous.low and latest.close > previous.low:
            swept = "sell_side"
        elif latest.high > previous.high and latest.close < previous.high:
            swept = "buy_side"
    return LiquidityMap(support, resistance, support_distance, resistance_distance,
                        resistance_distance > 0.002, support_distance > 0.002, swept)
