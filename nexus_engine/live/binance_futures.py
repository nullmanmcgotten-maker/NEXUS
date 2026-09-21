from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from ..config import Settings


class BinanceFuturesAdapter:
    """Signed Binance USD-M Futures REST adapter."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self.base_url = "https://testnet.binancefuture.com" if settings.binance_testnet else settings.binance_base_url

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, signed: bool = False) -> Any:
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
        response = self.session.request(method, f"{self.base_url}{path}", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def ping(self) -> bool:
        try:
            self._request("GET", "/fapi/v1/ping")
            return True
        except requests.RequestException:
            return False

    def fetch_account(self) -> dict[str, Any]:
        return self._request("GET", "/fapi/v2/account", signed=True)

    def fetch_exchange_info(self) -> dict[str, Any]:
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def fetch_open_orders(self, symbol: Optional[str] = None) -> list[dict[str, Any]]:
        return self._request("GET", "/fapi/v1/openOrders", {"symbol": symbol} if symbol else {}, signed=True)

    def fetch_order(self, symbol: str, order_id: Optional[int] = None, client_order_id: Optional[str] = None) -> dict[str, Any]:
        params: dict[str, Any] = {"symbol": symbol}
        if order_id is not None:
            params["orderId"] = order_id
        if client_order_id:
            params["origClientOrderId"] = client_order_id
        return self._request("GET", "/fapi/v1/order", params, signed=True)

    def create_order(self, params: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/fapi/v1/order", params, signed=True)

    def cancel_order(self, symbol: str, order_id: int) -> dict[str, Any]:
        return self._request("DELETE", "/fapi/v1/order", {"symbol": symbol, "orderId": order_id}, signed=True)
