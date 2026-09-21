from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Settings:
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    binance_base_url: str = "https://fapi.binance.com"
    binance_testnet: bool = False
    symbol: str = "BTCUSDT"
    account_capital: float = 10000.0
    max_risk_per_trade: float = 0.004
    max_daily_loss: float = 0.02
    max_open_positions: int = 3
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    enable_live_orders: bool = False
    use_realtime_data: bool = False


def load_settings() -> Settings:
    return Settings(
        binance_api_key=os.getenv("BINANCE_API_KEY"),
        binance_api_secret=os.getenv("BINANCE_API_SECRET"),
        binance_base_url=os.getenv("BINANCE_BASE_URL", "https://fapi.binance.com"),
        binance_testnet=os.getenv("BINANCE_TESTNET", "false").lower() == "true",
        symbol=os.getenv("NEXUS_SYMBOL", "BTCUSDT"),
        account_capital=float(os.getenv("NEXUS_ACCOUNT_CAPITAL", "10000.0")),
        max_risk_per_trade=float(os.getenv("NEXUS_MAX_RISK_PER_TRADE", "0.004")),
        max_daily_loss=float(os.getenv("NEXUS_MAX_DAILY_LOSS", "0.02")),
        max_open_positions=int(os.getenv("NEXUS_MAX_OPEN_POSITIONS", "3")),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        enable_live_orders=os.getenv("NEXUS_ENABLE_LIVE_ORDERS", "false").lower() == "true",
        use_realtime_data=os.getenv("NEXUS_USE_REALTIME_DATA", "false").lower() == "true",
    )
