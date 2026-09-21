from __future__ import annotations

import requests
from typing import Optional


class TelegramNotifier:
    def __init__(self, token: Optional[str], chat_id: Optional[str]):
        self.token, self.chat_id = token, chat_id

    def send(self, text: str) -> bool:
        if not self.token or not self.chat_id:
            return False
        response = requests.post(f"https://api.telegram.org/bot{self.token}/sendMessage",
                                 json={"chat_id": self.chat_id, "text": text}, timeout=10)
        return response.ok

    def approval(self, symbol: str, side: str, quantity: float, entry: float, stop: float, target: float, client_order_id: str) -> bool:
        return self.send(f"NEXUS APPROVAL\n{symbol} {side}\nQty: {quantity}\nEntry: {entry}\nSL: {stop}\nTP: {target}\nOrder: {client_order_id}")

    def lifecycle(self, client_order_id: str, state: str, detail: str = "") -> bool:
        return self.send(f"NEXUS ORDER {state}\n{client_order_id}\n{detail}")
