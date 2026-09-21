from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Optional


GateState = Literal["PASS", "BLOCK"]
OrderState = Literal["CREATED", "SUBMITTED", "PARTIALLY_FILLED", "FILLED", "CANCELED", "REJECTED", "UNKNOWN"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AccountValidation:
    ok: bool
    can_trade: bool = False
    account_type: Optional[str] = None
    wallet_balance: float = 0.0
    available_balance: float = 0.0
    positions: int = 0
    reason_codes: list[str] = field(default_factory=list)
    checked_at: str = field(default_factory=utc_now)


@dataclass
class RiskGate:
    state: GateState
    risk_amount: float
    daily_pnl: float
    open_positions: int
    expected_rr: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class ExecutionGate:
    state: GateState
    symbol: str
    side: str
    quantity: float
    spread_bps: float
    estimated_cost: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class OrderRecord:
    client_order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    state: OrderState = "CREATED"
    exchange_order_id: Optional[str] = None
    entry_price: Optional[float] = None
    stop_order_id: Optional[str] = None
    target_order_id: Optional[str] = None
    updated_at: str = field(default_factory=utc_now)
    raw: dict[str, Any] = field(default_factory=dict)
