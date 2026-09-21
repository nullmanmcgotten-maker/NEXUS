from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from nexus_engine.config import Settings


@dataclass
class PositionSnapshot:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    unrealized_pnl: float
    leverage: int


class RiskGovernor:
    """Risk policy and kill-switch logic for live execution."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def max_trade_risk(self, account_balance: float) -> float:
        return account_balance * self.settings.max_risk_per_trade

    def max_daily_loss(self, account_balance: float) -> float:
        return account_balance * self.settings.max_daily_loss

    def check_trade_allowed(
        self,
        account_balance: float,
        daily_pnl: float,
        open_positions: int,
        estimated_risk: float,
        expected_rr: float,
    ) -> tuple[bool, List[str]]:
        reasons: List[str] = []
        if daily_pnl <= -self.max_daily_loss(account_balance):
            reasons.append("daily_loss_limit_reached")
        if open_positions >= self.settings.max_open_positions:
            reasons.append("max_open_positions_reached")
        if estimated_risk > self.max_trade_risk(account_balance):
            reasons.append("trade_risk_exceeds_limit")
        if expected_rr < 1.5:
            reasons.append("risk_reward_below_threshold")

        return len(reasons) == 0, reasons

    def validate_position_limit(self, positions: List[PositionSnapshot], new_symbol: str) -> bool:
        same_symbol = sum(1 for p in positions if p.symbol == new_symbol)
        return same_symbol < self.settings.max_open_positions
