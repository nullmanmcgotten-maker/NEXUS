from __future__ import annotations

from .models import MarketSnapshot, ExecutionResult


def estimate_execution_cost(snapshot: MarketSnapshot, units: float) -> ExecutionResult:
    """Estimate fees, spread, and slippage costs using simple but realistic assumptions."""
    mid = (snapshot.bid + snapshot.ask) / 2.0
    spread_cost = abs(snapshot.ask - snapshot.bid) * units
    slippage_cost = max(0.0, abs(snapshot.price - mid) * units * 0.7)

    expected_cost = spread_cost + slippage_cost
    if snapshot.spread_bps > 4.5:
        quality = "poor"
    elif snapshot.spread_bps > 2.0:
        quality = "fair"
    else:
        quality = "good"

    return ExecutionResult(
        spread_cost=spread_cost,
        slippage_cost=slippage_cost,
        expected_cost=expected_cost,
        quality=quality,
    )


def execution_quality(snapshot: MarketSnapshot, units: float) -> float:
    """Return a normalized execution-quality score from 0 to 1."""
    cost = estimate_execution_cost(snapshot, units)
    score = 1.0
    score -= min(cost.expected_cost / (snapshot.price * max(units, 1.0) * 0.02), 1.0)
    if snapshot.spread_bps > 2.5:
        score -= 0.2
    if snapshot.depth_usd < 100000:
        score -= 0.2
    return max(0.0, min(1.0, score))
