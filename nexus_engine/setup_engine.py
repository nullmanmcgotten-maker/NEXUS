from __future__ import annotations

from .execution import execution_quality
from .market_regime import classify_regime, regime_score
from .models import MarketSnapshot, TradeApproval, TradePlan
from .orderflow import liquidity_score, order_flow_signal
from .risk import position_units_for_risk, risk_reward


def _approval_reasons(snapshot: MarketSnapshot) -> list[str]:
    reasons: list[str] = []
    regime = classify_regime(snapshot)
    if regime in {"trend_up", "trend_down", "volatility_compression"}:
        reasons.append(f"regime:{regime}")
    if snapshot.session_quality >= 0.5:
        reasons.append("session_quality:good")
    else:
        reasons.append("session_quality:weak")
    if snapshot.spread_bps <= 3.0:
        reasons.append("spread:acceptable")
    if snapshot.depth_usd >= 100000:
        reasons.append("depth:acceptable")
    return reasons


def generate_trade_plan(
    snapshot: MarketSnapshot,
    account_capital: float,
    risk_fraction: float = 0.004,
    rr_floor: float = 1.8,
) -> TradeApproval:
    """Generate a trade plan if the signal clears all mandatory gates."""
    vetoes: list[str] = []

    regime = classify_regime(snapshot)
    if regime in {"chop", "no_trade"}:
        vetoes.append("regime_disallows_trade")

    if snapshot.spread_bps > 4.0:
        vetoes.append("spread_too_wide")

    if snapshot.depth_usd < 100000:
        vetoes.append("insufficient_depth")

    if snapshot.session_quality < 0.35:
        vetoes.append("weak_session")

    if snapshot.volatility_pct < 0.2 and snapshot.bb_width_pct < 0.08:
        vetoes.append("too_low_volatility")

    if snapshot.funding_rate > 0.0006:
        vetoes.append("funding_pressure_bias")

    liq = liquidity_score(snapshot)
    flow = order_flow_signal(snapshot)

    if liq < 0.45:
        vetoes.append("liquidity_score_too_low")

    if flow["score"] == 0:
        vetoes.append("order_flow_not_confirmed")

    # Direction selection
    if snapshot.higher_tf_bias == "bullish" and flow["direction"] in {"bullish", "neutral"}:
        side = "long"
    elif snapshot.higher_tf_bias == "bearish" and flow["direction"] in {"bearish", "neutral"}:
        side = "short"
    else:
        side = "long" if flow["direction"] == "bullish" else "short" if flow["direction"] == "bearish" else None

    if side is None:
        vetoes.append("no_clear_direction")
        return TradeApproval(False, veto_reasons=vetoes)

    if snapshot.higher_tf_bias == "neutral" and regime not in {"trend_up", "trend_down"}:
        vetoes.append("neutral_bias_without_structure")

    # Price / risk model
    mid = (snapshot.bid + snapshot.ask) / 2.0
    if side == "long":
        entry = snapshot.ask * 1.0002
        stop = snapshot.bid * 0.997
    else:
        entry = snapshot.bid * 0.9998
        stop = snapshot.ask * 1.003

    if side == "long":
        target = entry * (1 + (rr_floor * abs(entry - stop) / entry))
    else:
        target = entry * (1 - (rr_floor * abs(entry - stop) / entry))

    rr = risk_reward(entry, stop, target)
    if rr < rr_floor:
        vetoes.append("risk_reward_too_low")

    position_size = position_units_for_risk(entry, stop, account_capital, risk_fraction)
    if position_size <= 0:
        vetoes.append("position_size_zero")

    exec_score = execution_quality(snapshot, position_size)
    if exec_score < 0.5:
        vetoes.append("execution_quality_too_low")

    score = (
        regime_score(snapshot) * 0.35
        + liq * 0.2
        + max(0.0, flow["score"]) * 0.25
        + exec_score * 0.2
    )

    if score < 0.65:
        vetoes.append("approval_score_too_low")

    if vetoes:
        return TradeApproval(False, veto_reasons=vetoes)

    plan = TradePlan(
        symbol=snapshot.symbol,
        side=side,
        entry=round(entry, 6),
        stop=round(stop, 6),
        target=round(target, 6),
        position_units=round(position_size, 6),
        score=round(score, 4),
        regime=regime,
        reasons=_approval_reasons(snapshot),
    )
    return TradeApproval(True, trade=plan)
