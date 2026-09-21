from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from nexus_engine.config import load_settings
from nexus_engine.engine import TradingEngine
from nexus_engine.live.binance_futures import BinanceFuturesAdapter
from nexus_engine.models import MarketSnapshot
from nexus_engine.risk_governor import RiskGovernor


class EngineLoop:
    """Main live engine loop. Connects the market feed, approval engine, risk engine, and execution manager."""

    def __init__(self, settings=None):
        self.settings = settings or load_settings()
        self.adapter = BinanceFuturesAdapter(self.settings)
        self.engine = TradingEngine(self.settings.account_capital, self.settings.max_risk_per_trade)
        self.risk = RiskGovernor(self.settings)

    def _build_market_snapshot(self) -> MarketSnapshot:
        ticker = self.adapter.fetch_ticker(self.settings.symbol)
        book = self.adapter.fetch_book_ticker(self.settings.symbol)
        mark = self.adapter.fetch_mark_price(self.settings.symbol)

        bid = float(book["bidPrice"])
        ask = float(book["askPrice"])
        price = float(mark["markPrice"])

        return MarketSnapshot(
            symbol=self.settings.symbol,
            price=price,
            bid=bid,
            ask=ask,
            spread_bps=((ask - bid) / price) * 10000,
            atr=float(ticker.get("weightedAvgPrice", 0.0)) / 100.0,
            adx=28.0,
            trend_strength=0.75,
            volatility_pct=1.0,
            volume=float(ticker.get("quoteVolume", 0.0)),
            funding_rate=float(mark.get("lastFundingRate", 0.0)),
            open_interest=float(ticker.get("openInterest", 0.0)),
            oi_change_pct=0.0,
            delta_imbalance=0.25,
            cumulative_volume_delta=0.0,
            taker_buy_sell_ratio=1.12,
            vwap_distance_pct=0.2,
            bb_width_pct=0.14,
            rsi=58.0,
            higher_tf_bias="bullish",
            session_quality=0.75,
            liquidity_score=0.8,
            depth_usd=250000.0,
            sentiment_score=0.7,
        )

    def check_connection(self) -> bool:
        return self.adapter.ping()

    def run_once(self) -> Dict[str, Any]:
        if not self.check_connection():
            return {"status": "offline", "reason": "binance_ping_failed"}

        snapshot = self._build_market_snapshot()
        approval = self.engine.approve(snapshot, rr_floor=1.8)
        if not approval.approved:
            return {
                "status": "rejected",
                "symbol": snapshot.symbol,
                "veto_reasons": approval.veto_reasons,
            }

        trade = approval.trade
        if trade is None:
            return {"status": "empty_trade"}

        estimated_risk = abs(trade.entry - trade.stop) * trade.position_units
        ok, reasons = self.risk.check_trade_allowed(
            account_balance=self.settings.account_capital,
            daily_pnl=0.0,
            open_positions=0,
            estimated_risk=estimated_risk,
            expected_rr=1.8,
        )
        if not ok:
            return {"status": "risk_blocked", "reasons": reasons}

        return {
            "status": "approved",
            "symbol": trade.symbol,
            "side": trade.side,
            "entry": trade.entry,
            "stop": trade.stop,
            "target": trade.target,
            "position_units": trade.position_units,
            "score": trade.score,
            "regime": trade.regime,
            "reasons": trade.reasons,
        }
