from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class MarketSnapshot:
    symbol: str
    price: float
    bid: float
    ask: float
    spread_bps: float
    atr: float
    adx: float
    trend_strength: float
    volatility_pct: float
    volume: float
    rvix: Optional[float] = None
    funding_rate: float = 0.0
    open_interest: float = 0.0
    oi_change_pct: float = 0.0
    delta_imbalance: float = 0.0
    cumulative_volume_delta: float = 0.0
    taker_buy_sell_ratio: float = 1.0
    vwap_distance_pct: float = 0.0
    bb_width_pct: float = 0.0
    rsi: float = 50.0
    higher_tf_bias: str = "neutral"
    session_quality: float = 0.5
    liquidity_score: float = 0.0
    depth_usd: float = 0.0
    sentiment_score: float = 0.0


@dataclass
class TradePlan:
    symbol: str
    side: Literal["long", "short"]
    entry: float
    stop: float
    target: float
    position_units: float
    score: float
    regime: str
    reasons: list[str] = field(default_factory=list)


@dataclass
class TradeApproval:
    approved: bool
    trade: Optional[TradePlan] = None
    veto_reasons: list[str] = field(default_factory=list)


@dataclass
class ExecutionResult:
    spread_cost: float
    slippage_cost: float
    expected_cost: float
    quality: str
