from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .live_models import AccountValidation


@dataclass
class AccountValidator:
    adapter: Any

    def validate(self, symbol: Optional[str] = None) -> AccountValidation:
        try:
            account = self.adapter.fetch_account()
            positions = [p for p in account.get("positions", []) if abs(float(p.get("positionAmt", 0))) > 0]
            wallet = float(account.get("totalWalletBalance", 0))
            available = float(account.get("availableBalance", 0))
            can_trade = bool(account.get("canTrade", False))
            reasons: list[str] = []
            if not can_trade:
                reasons.append("exchange_can_trade_false")
            if available <= 0:
                reasons.append("no_available_balance")
            if symbol and not any(p.get("symbol") == symbol for p in account.get("positions", [])):
                # A missing position is normal; symbol validation is done through exchangeInfo.
                pass
            return AccountValidation(
                ok=not reasons,
                can_trade=can_trade and not reasons,
                account_type=account.get("accountType"),
                wallet_balance=wallet,
                available_balance=available,
                positions=len(positions),
                reason_codes=reasons,
            )
        except Exception as exc:
            return AccountValidation(ok=False, reason_codes=[f"account_validation_error:{type(exc).__name__}"])
