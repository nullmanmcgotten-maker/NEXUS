from __future__ import annotations

from typing import Literal

from .models import MarketSnapshot


Regime = Literal[
    "trend_up",
    "trend_down",
    "range",
    "volatility_compression",
    "volatility_expansion",
    "chop",
    "no_trade",
]


def classify_regime(snapshot: MarketSnapshot) -> Regime:
    """Classify the current regime based on trend, volatility, and structure."""
    if snapshot.adx >= 28 and snapshot.trend_strength >= 0.6:
        return "trend_up" if snapshot.higher_tf_bias == "bullish" else "trend_down"

    if snapshot.bb_width_pct < 0.15 and snapshot.volatility_pct < 0.8:
        return "volatility_compression"

    if snapshot.volatility_pct > 1.5 and snapshot.volume > 0:
        return "volatility_expansion"

    if snapshot.adx < 20 and abs(snapshot.vwap_distance_pct) < 0.5 and abs(snapshot.rsi - 50) < 15:
        return "range"

    if snapshot.volatility_pct < 0.35 and abs(snapshot.rsi - 50) < 10:
        return "chop"

    return "no_trade"


def regime_score(snapshot: MarketSnapshot) -> float:
    """Return a normalized regime quality score for approval logic."""
    regime = classify_regime(snapshot)
    base = {
        "trend_up": 0.9,
        "trend_down": 0.9,
        "range": 0.6,
        "volatility_compression": 0.75,
        "volatility_expansion": 0.7,
        "chop": 0.2,
        "no_trade": 0.0,
    }.get(regime, 0.0)

    if snapshot.session_quality < 0.2:
        base *= 0.7

    return max(0.0, min(1.0, base))
