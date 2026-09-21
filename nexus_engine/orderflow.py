from __future__ import annotations

from .models import MarketSnapshot


def order_flow_signal(snapshot: MarketSnapshot) -> dict:
    """Create a simple but useful order-flow summary from the market state."""
    delta = snapshot.delta_imbalance
    cfd = snapshot.cumulative_volume_delta
    taker_ratio = snapshot.taker_buy_sell_ratio

    score = 0.0
    direction = "neutral"

    if delta > 0.3:
        score += 0.5
        direction = "bullish"
    elif delta < -0.3:
        score += 0.5
        direction = "bearish"

    if cfd > 0:
        score += 0.25
    elif cfd < 0:
        score -= 0.25

    if taker_ratio > 1.15:
        score += 0.15
    elif taker_ratio < 0.85:
        score -= 0.15

    return {
        "direction": direction,
        "score": max(-1.0, min(1.0, score)),
        "delta_imbalance": delta,
        "cumulative_volume_delta": cfd,
        "taker_buy_sell_ratio": taker_ratio,
    }


def liquidity_score(snapshot: MarketSnapshot) -> float:
    """Return a normalized score from 0 to 1."""
    score = 0.0
    score += min(snapshot.liquidity_score, 1.0)
    score += min(snapshot.depth_usd / 250000.0, 1.0) * 0.5
    if snapshot.spread_bps < 3.0:
        score += 0.25
    if snapshot.session_quality > 0.5:
        score += 0.25
    return max(0.0, min(1.0, score / 2.0))
