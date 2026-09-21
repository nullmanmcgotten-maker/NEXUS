from __future__ import annotations

from .expertise_engine import PerpetualExpertiseEngine
from .journal import TradeJournal
from .order_lifecycle import LiveOrderLifecycle


class LiveDecisionEngine:
    def __init__(self, settings, adapter):
        self.settings = settings
        self.adapter = adapter
        self.expertise = PerpetualExpertiseEngine(adapter)
        self.lifecycle = LiveOrderLifecycle(settings)
        self.journal = TradeJournal()

    def run_once(self):
        thesis = self.expertise.analyze(self.settings.symbol)
        self.journal.record_analysis(self.settings.symbol, thesis)
        if not thesis.approved:
            return thesis
        quantity = self.lifecycle.risk_position_size(thesis.entry, thesis.stop)
        risk_gate = self.lifecycle.risk_gate(abs(thesis.entry - thesis.stop) * quantity, 0.0, 0, (abs(thesis.target - thesis.entry) / abs(thesis.entry - thesis.stop)))
        if risk_gate.state != "PASS":
            self.journal.record_gate(self.settings.symbol, "risk", risk_gate)
            return thesis
        return self.lifecycle.execute_entry(self.settings.symbol, thesis.side, quantity, thesis.entry, thesis.stop, thesis.target, 0.0, 0.0, risk_gate, thesis)
