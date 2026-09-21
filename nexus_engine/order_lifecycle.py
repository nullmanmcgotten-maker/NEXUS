from __future__ import annotations

import uuid
from typing import Any

from .account_validator import AccountValidator
from .journal import TradeJournal
from .live.binance_futures import BinanceFuturesAdapter
from .live_models import ExecutionGate, OrderRecord, RiskGate
from .risk_governor import RiskGovernor
from .telegram_notifier import TelegramNotifier


class LiveOrderLifecycle:
    def __init__(self, settings: Any):
        self.settings = settings
        self.adapter = BinanceFuturesAdapter(settings)
        self.validator = AccountValidator(self.adapter)
        self.risk = RiskGovernor(settings)
        self.journal = TradeJournal()
        self.telegram = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)

    def validate_account(self):
        return self.validator.validate(self.settings.symbol)

    def risk_gate(self, risk_amount: float, daily_pnl: float, open_positions: int, expected_rr: float) -> RiskGate:
        balance = self.validate_account().available_balance
        ok, reasons = self.risk.check_trade_allowed(balance, daily_pnl, open_positions, risk_amount, expected_rr)
        return RiskGate("PASS" if ok else "BLOCK", risk_amount, daily_pnl, open_positions, expected_rr, reasons)

    def execute_entry(self, symbol: str, side: str, quantity: float, entry: float, stop: float, target: float,
                      spread_bps: float, estimated_cost: float, risk_gate: RiskGate) -> OrderRecord:
        account = self.validate_account()
        if not account.ok or not account.can_trade:
            raise RuntimeError(f"Account blocked: {account.reason_codes}")
        if risk_gate.state != "PASS":
            raise RuntimeError(f"Risk gate blocked: {risk_gate.reasons}")
        if not self.settings.enable_live_orders:
            raise RuntimeError("NEXUS_ENABLE_LIVE_ORDERS is false")

        client_id = f"NEXUS_{uuid.uuid4().hex[:20]}"
        record = OrderRecord(client_id, symbol, side.upper(), "MARKET", quantity)
        self.journal.record(record)
        self.telegram.approval(symbol, side, quantity, entry, stop, target, client_id)
        try:
            raw = self.adapter.create_order({"symbol": symbol, "side": side.upper(), "type": "MARKET", "quantity": quantity, "newClientOrderId": client_id})
            record.state = "SUBMITTED"
            record.exchange_order_id = str(raw.get("orderId"))
            record.raw = raw
            self.journal.record(record)
            self.telegram.lifecycle(client_id, "SUBMITTED", str(raw.get("orderId")))
            return record
        except Exception as exc:
            record.state = "UNKNOWN"
            record.raw = {"error": str(exc)}
            self.journal.record(record)
            self.telegram.lifecycle(client_id, "UNKNOWN", str(exc))
            raise
