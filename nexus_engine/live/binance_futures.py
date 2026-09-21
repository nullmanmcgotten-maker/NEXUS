from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Optional
from urllib.parse import urlencode

import requests

from ..config import Settings


class BinanceFuturesAdapter:
    """Complete USD-M Futures REST market-data adapter."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self.base_url = "https://testnet.binancefuture.com" if settings.binance_testnet else settings.binance_base_url

    def _request(self, method: str, path: str, params: Optional[dict[str, Any]] = None, signed: bool = False) -> Any:
        params = dict(params or {})
        headers: dict[str, str] = {}
        if signed:
            if not self.settings.binance_api_key or not self.settings.binance_api_secret:
                raise ValueError("Binance API credentials are required")
            params.setdefault("timestamp", int(time.time() * 1000))
            params.setdefault("recvWindow", 5000)
            query = urlencode(params, doseq=True)
            params["signature"] = hmac.new(self.settings.binance_api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
            headers["X-MBX-APIKEY"] = self.settings.binance_api_key
        response = self.session.request("GET" if method == "GET" else method, f"{self.base_url}{path}", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def fetch_klines(self, interval: str, limit: int, symbol: str):
        return self._request("GET", "/fapi/v1/klines", {"symbol": symbol, "interval": interval, "limit": min(limit, 1500)})

    def fetch_aggregate_trades(self, symbol: str, limit: int = 1000):
        return self._request("GET", "/fapi/v1/aggTrades", {"symbol": symbol, "limit": min(limit, 1000)})

    def fetch_mark_price(self, symbol: str):
        return self._request("GET", "/fapi/v1/premiumIndex", {"symbol": symbol})

    def fetch_open_interest(self, symbol: str):
        return self._request("GET", "/fapi/v1/openInterest", {"symbol": symbol})

    def fetch_open_interest_history(self, symbol: str, period: str = "5m", limit: int = 30):
        return self._request("GET", "/futures/data/openInterestHist", {"symbol": symbol, "period": period, "limit": min(limit, 500)})

    def fetch_force_orders(self, symbol: str, limit: int = 100):
        return self._request("GET", "/fapi/v1/forceOrders", {"symbol": symbol, "limit": min(limit, 100)})

    def fetch_exchange_info(self):
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def fetch_depth(self, symbol: str, limit: int = 100):
        return self._request("GET", "/fapi/v1/depth", {"symbol": symbol, "limit": limit})
