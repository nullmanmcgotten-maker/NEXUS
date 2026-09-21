from __future__ import annotations

from .signal_models import OrderFlowPersistence


def analyze_flow_persistence(flows: list[float], price_changes: list[float]) -> OrderFlowPersistence:
    if not flows:
        return OrderFlowPersistence(0, 0, 0, "none", False)
    current = flows[-1]
    window = flows[-12:]
    rolling = sum(window) / len(window)
    same_direction = sum(1 for x in window if x * rolling > 0) / len(window)
    recent_price = sum(price_changes[-12:]) if price_changes else 0
    aggressive = abs(rolling) > 0.12
    absorption = "none"
    if aggressive and abs(recent_price) < 0.001:
        absorption = "sell_absorption" if rolling < 0 else "buy_absorption"
    exhaustion = aggressive and abs(current) < abs(rolling) * 0.35
    return OrderFlowPersistence(current, rolling, same_direction, absorption, exhaustion)
