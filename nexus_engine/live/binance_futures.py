from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from .config import Settings


class BinanceFuturesAdapter:
    """Live Binance Futures adapter using REST endpoints for market data and account access."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self.base_url = settings.binance_base_url
        if settings.binance_testnet:
            self.base_url = "https://testnet.binancefuture.com"

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        resp = self.session.get(f"{self.base_url}{path}", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def ping(self) -> bool:
        try:
            self._get("/fapi/v1/ping")
            return True
        except Exception:
            return False

    def fetch_ticker(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        return self._get(
            "/fapi/v1/ticker/24hr",
            params={"symbol": symbol or self.settings.symbol},
        )

    def fetch_book_ticker(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        return self._get(
            "/fapi/v1/ticker/bookTicker",
            params={"symbol": symbol or self.settings.symbol},
        )

    def fetch_mark_price(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        return self._get(
            "/fapi/v1/premiumIndex",
            params={"symbol": symbol or self.settings.symbol},
        )

    def fetch_klines(self, interval: str = "15m", limit: int = 200, symbol: Optional[str] = None):
        return self._get(
            "/fapi/v1/klines",
            params={
                "symbol": symbol or self.settings.symbol,
                "interval": interval,
                "limit": limit,
            },
        )

    def fetch_account_balance(self) -> Dict[str, Any]:
        if not self.settings.binance_api_key or not self.settings.binance_api_secret:
            raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET must be set to fetch account state.")

        # Use signed request with HMAC SHA256 for futures account data.
        # This is intentionally strict; the live adapter should validate and log before any order placement.
        from hashlib import sha256
        from hmac import new as hmac_new
        import time
        from urllib.parse import urlencode

        query = {
            "timestamp": int(time.time() * 1000),
            "recvWindow": 60000,
        }
        query_string = urlencode(query)
        signature = hmac_new(
            self.settings.binance_api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            sha256,
        ).hexdigest()

        headers = {"X-MAX-APIKEY": self.settings.binance_api_key}
        resp = self.session.get(
            f"{self.base_url}/fapi/v2/account",
            params={**query, "signature": signature},
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def create_order(
        self,
        side: str,
        quantity: float,
        order_type: str = "MARKET",
        symbol: Optional[str] = None,
        reduce_only: bool = False,
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        if not self.settings.binance_api_key or not self.settings.binance_api_secret:
            raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET must be set to place orders.")

        from hashlib import sha256
        from hmac import new as hmac_new
        import time
        from urllib.parse import urlencode

        payload = {
            "symbol": symbol or self.settings.symbol,
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": quantity,
            "timestamp": int(time.time() * 1000),
            "recvWindow": 60000,
        }
        if reduce_only:
            payload["reduceOnly"] = "true"
        if price is not None:
            payload["price"] = round(price, 2)

        query_string = urlencode(payload)
        signature = hmac_new(
            self.settings.binance_api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            sha256,
        ).hexdigest()

        headers = {"X-MAX-APIKEY": self.settings.binance_api_key}
        resp = self.session.post(
            f"{self.base_url}/fapi/v1/order",
            params={**payload, "signature": signature},
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
