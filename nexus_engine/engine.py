from __future__ import annotations

from .models import MarketSnapshot, TradeApproval
from .setup_engine import generate_trade_plan


class TradingEngine:
    """Simple orchestration layer for a regime-aware trading signal engine."""

    def __init__(self, account_capital: float, risk_fraction: float = 0.004):
        self.account_capital = account_capital
        self.risk_fraction = risk_fraction

    def approve(self, snapshot: MarketSnapshot, rr_floor: float = 1.8) -> TradeApproval:
        return generate_trade_plan(
            snapshot=snapshot,
            account_capital=self.account_capital,
            risk_fraction=self.risk_fraction,
            rr_floor=rr_floor,
        )

    def screen(self, snapshots: list[MarketSnapshot], rr_floor: float = 1.8) -> list[TradeApproval]:
        return [self.approve(s, rr_floor=rr_floor) for s in snapshots]
