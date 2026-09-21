from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .market_math import Candle, atr, bollinger_width, ema, realized_volatility, rsi, vwap


@dataclass(frozen=True)
class TimeframeFeatures:
    interval: str
    close: float
    ema_fast: float
    ema_slow: float
    atr: float
    rsi: float
    bb_width: float
    vwap: float
    volatility: float
    trend: str


def calculate_features(interval: str, candles: list[Candle]) -> TimeframeFeatures:
    closes = [c.close for c in candles]
    fast, slow = ema(closes, 20), ema(closes, 50)
    trend = "up" if fast > slow and closes[-1] >= fast else "down" if fast < slow and closes[-1] <= fast else "range"
    return TimeframeFeatures(interval, closes[-1], fast, slow, atr(candles), rsi(candles), bollinger_width(candles), vwap(candles), realized_volatility(candles), trend)


def volume_stats(candles: list[Candle]) -> dict[str, float]:
    if not candles:
        return {"rvol": 0.0, "volume": 0.0, "taker_ratio": 1.0}
    current = candles[-1].quote_volume or candles[-1].volume * candles[-1].close
    history = [c.quote_volume or c.volume * c.close for c in candles[-21:-1]]
    average = sum(history) / len(history) if history else current
    taker = candles[-1].taker_buy_quote_volume or candles[-1].taker_buy_volume * candles[-1].close
    return {"rvol": current / average if average else 0.0, "volume": current, "taker_ratio": taker / current if current else 0.5}
