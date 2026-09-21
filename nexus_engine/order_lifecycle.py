from __future__ import annotations

from .live_models import RiskGate, OrderRecord


class LiveOrderLifecycle:
    # Existing constructor and account/risk methods remain unchanged.
    def thesis_gate(self, thesis) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        if not thesis.live_eligible:
            reasons.append("thesis_not_A_grade_or_expired")
        if thesis.expected_net_r < 1.8:
            reasons.append("expected_net_r_below_floor")
        return not reasons, reasons

    def execute_thesis(self, thesis, quantity: float, risk_gate: RiskGate) -> OrderRecord:
        ok, reasons = self.thesis_gate(thesis)
        if not ok:
            raise RuntimeError(f"Thesis blocked: {reasons}")
        if risk_gate.state != "PASS":
            raise RuntimeError(f"Risk gate blocked: {risk_gate.reasons}")
        return self.execute_entry(
            thesis.feature_snapshot["symbol"], thesis.side, quantity,
            thesis.entry, thesis.stop, thesis.target, 0.0, 0.0, risk_gate, thesis,
        )
