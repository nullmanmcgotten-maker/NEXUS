from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OrderFlow:
    delta: float
    buy_volume: float
    sell_volume: float
    imbalance: float
    large_trade_bias: str


@dataclass(frozen=True)
class PerpAnalysis:
    funding: float
    funding_percentile: float
    open_interest: float
    oi_change_pct: float
    basis_pct: float
    liquidation_buy: float
    liquidation_sell: float
    crowding: str


@dataclass(frozen=True)
class Thesis:
    approved: bool
    setup: str
    side: str
    confidence: float
    regime: str
    entry: float
    stop: float
    target: float
    reasons: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    invalidations: tuple[str, ...] = field(default_factory=tuple)
    features: dict[str, Any] = field(default_factory=dict)


def aggregate_order_flow(trades: list[dict[str, Any]]) -> OrderFlow:
    buy = sell = 0.0
    large_buy = large_sell = 0.0
    for trade in trades:
        qty = float(trade.get("quoteQty") or float(trade.get("qty", 0)) * float(trade.get("price", 0)))
        # Binance aggTrades: m=True means buyer is maker, so aggressor is sell.
        if bool(trade.get("m", False)):
            sell += qty
            large_sell += qty if qty >= 10000 else 0
        else:
            buy += qty
            large_buy += qty if qty >= 10000 else 0
    total = buy + sell
    return OrderFlow(buy - sell, buy, sell, (buy - sell) / total if total else 0.0,
                     "buy" if large_buy > large_sell else "sell" if large_sell > large_buy else "balanced")


def analyze_perpetual(mark: dict[str, Any], oi_now: float, oi_previous: float, liquidations: list[dict[str, Any]]) -> PerpAnalysis:
    funding = float(mark.get("lastFundingRate", 0.0))
    price = float(mark.get("markPrice", 0.0))
    index = float(mark.get("indexPrice", price))
    basis = ((price - index) / index * 100) if index else 0.0
    oi_change = ((oi_now - oi_previous) / oi_previous * 100) if oi_previous else 0.0
    buy_liq = sum(float(x.get("origQty", 0)) for x in liquidations if x.get("side") == "SELL")
    sell_liq = sum(float(x.get("origQty", 0)) for x in liquidations if x.get("side") == "BUY")
    crowding = "long_crowded" if funding > 0.0004 and oi_change > 1 else "short_crowded" if funding < -0.0004 and oi_change > 1 else "neutral"
    return PerpAnalysis(funding, 0.5, oi_now, oi_change, basis, buy_liq, sell_liq, crowding)
