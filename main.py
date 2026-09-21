from __future__ import annotations

from nexus_engine.models import MarketSnapshot
from nexus_engine.engine import TradingEngine


sample = MarketSnapshot(
    symbol="BTCUSDT",
    price=65000.0,
    bid=64998.0,
    ask=65002.0,
    spread_bps=0.6,
    atr=1200.0,
    adx=33.0,
    trend_strength=0.82,
    volatility_pct=0.94,
    volume=2_400_000,
    funding_rate=0.00018,
    open_interest=58_000_000,
    oi_change_pct=3.2,
    delta_imbalance=0.42,
    cumulative_volume_delta=120000,
    taker_buy_sell_ratio=1.18,
    vwap_distance_pct=0.12,
    bb_width_pct=0.11,
    rsi=58,
    higher_tf_bias="bullish",
    session_quality=0.78,
    liquidity_score=0.8,
    depth_usd=250000,
    sentiment_score=0.72,
)


def main() -> None:
    engine = TradingEngine(account_capital=10000.0, risk_fraction=0.004)
    approval = engine.approve(sample, rr_floor=1.8)

    if approval.approved:
        trade = approval.trade
        print("TRADE APPROVED")
        print(f"Symbol: {trade.symbol}")
        print(f"Side: {trade.side}")
        print(f"Entry: {trade.entry}")
        print(f"Stop: {trade.stop}")
        print(f"Target: {trade.target}")
        print(f"Units: {trade.position_units}")
        print(f"Score: {trade.score}")
        print(f"Regime: {trade.regime}")
        print(f"Reasons: {trade.reasons}")
    else:
        print("TRADE REJECTED")
        print(approval.veto_reasons)


if __name__ == "__main__":
    main()
