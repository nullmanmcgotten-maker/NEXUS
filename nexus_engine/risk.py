from __future__ import annotations

from .models import MarketSnapshot


def risk_budget(account_capital: float, risk_fraction: float = 0.004) -> float:
    """Maximum capital allowed to risk per trade."""
    return account_capital * risk_fraction


def position_units_for_risk(
    entry_price: float,
    stop_price: float,
    account_capital: float,
    risk_fraction: float = 0.004,
) -> float:
    """Return position size in units based on stop distance and capital at risk."""
    if stop_price <= 0 or entry_price <= 0:
        return 0.0

    stop_distance = abs(entry_price - stop_price)
    if stop_distance <= 0:
        return 0.0

    risk_amount = risk_budget(account_capital, risk_fraction)
    return risk_amount / stop_distance


def risk_reward(entry: float, stop: float, target: float) -> float:
    """Risk-to-reward ratio."""
    risk = abs(entry - stop)
    reward = abs(target - entry)
    if risk <= 0:
        return 0.0
    return reward / risk
