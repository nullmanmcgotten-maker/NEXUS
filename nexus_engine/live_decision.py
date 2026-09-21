from __future__ import annotations

from .expertise_engine import PerpetualExpertiseEngine
from .journal import TradeJournal
from .order_lifecycle import LiveOrderLifecycle


class LiveDecisionEngine:
    def __init__(self, settings, adapter):
        self.settings = settings
        self.adapter = adapter
        self.journal = TradeJournal()
        self.expertise = PerpetualExpertiseEngine(adapter, self.journal)
        self.lifecycle = LiveOrderLifecycle(settings)

    def run_once(self):
        thesis = self.expertise.analyze(self.settings.symbol)
        if not thesis.live_eligible:
            self.journal.record_gate(self.settings.symbol, "thesis", thesis)
            return thesis
        account = self.lifecycle.validate_account()
        if not account.ok or not account.can_trade:
            self.journal.record_gate(self.settings.symbol, "account", account)
            return thesis
        quantity = self.lifecycle.risk_position_size(thesis.entry, thesis.stop)
        rr = abs(thesis.target - thesis.entry) / abs(thesis.entry - thesis.stop)
        risk_gate = self.lifecycle.risk_gate(abs(thesis.entry - thesis.stop) * quantity, 0.0, account.positions, rr)
        if risk_gate.state != "PASS":
            self.journal.record_gate(self.settings.symbol, "risk", risk_gate)
            return thesis
        return self.lifecycle.execute_thesis(thesis, quantity, risk_gate)
