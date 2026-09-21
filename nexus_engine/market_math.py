from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Candle:
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int = 0
    quote_volume: float = 0.0
    trades: int = 0
    taker_buy_volume: float = 0.0
    taker_buy_quote_volume: float = 0.0


def normalize_klines(rows: Iterable[Sequence[object]]) -> list[Candle]:
    result: list[Candle] = []
    for row in rows:
        if len(row) < 11:
            continue
        result.append(Candle(
            open_time=int(row[0]), open=float(row[1]), high=float(row[2]),
            low=float(row[3]), close=float(row[4]), volume=float(row[5]),
            close_time=int(row[6]), quote_volume=float(row[7]), trades=int(row[8]),
            taker_buy_volume=float(row[9]), taker_buy_quote_volume=float(row[10]),
        ))
    return result


def ema(values: Sequence[float], period: int) -> float:
    if not values:
        return 0.0
    alpha = 2.0 / (period + 1)
    value = values[0]
    for item in values[1:]:
        value = alpha * item + (1 - alpha) * value
    return value


def atr(candles: Sequence[Candle], period: int = 14) -> float:
    if len(candles) < 2:
        return 0.0
    trs = [max(c.high - c.low, abs(c.high - p.close), abs(c.low - p.close)) for p, c in zip(candles, candles[1:])]
    return sum(trs[-period:]) / min(period, len(trs))


def rsi(candles: Sequence[Candle], period: int = 14) -> float:
    changes = [c.close - p.close for p, c in zip(candles, candles[1:])]
    if not changes:
        return 50.0
    recent = changes[-period:]
    gains = sum(max(x, 0.0) for x in recent) / len(recent)
    losses = sum(max(-x, 0.0) for x in recent) / len(recent)
    if losses == 0:
        return 100.0 if gains else 50.0
    return 100.0 - (100.0 / (1.0 + gains / losses))


def bollinger_width(candles: Sequence[Candle], period: int = 20, deviations: float = 2.0) -> float:
    closes = [c.close for c in candles[-period:]]
    if len(closes) < 2:
        return 0.0
    mean = sum(closes) / len(closes)
    sd = math.sqrt(sum((x - mean) ** 2 for x in closes) / len(closes))
    return (2 * deviations * sd / mean) if mean else 0.0


def vwap(candles: Sequence[Candle]) -> float:
    volume = sum(c.volume for c in candles)
    return sum(((c.high + c.low + c.close) / 3) * c.volume for c in candles) / volume if volume else 0.0


def realized_volatility(candles: Sequence[Candle], period: int = 30) -> float:
    returns = [math.log(c.close / p.close) for p, c in zip(candles, candles[1:]) if p.close > 0 and c.close > 0]
    returns = returns[-period:]
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    return math.sqrt(sum((x - mean) ** 2 for x in returns) / (len(returns) - 1)) * math.sqrt(24 * 60)
