from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .signal_models import SignalDecision


class ConfidenceCalibrator:
    def __init__(self, journal: Any):
        self.journal = journal

    def adjust(self, setup: str, raw: float) -> float:
        stats = self.journal.setup_stats(setup)
        if stats["count"] < 30:
            return raw
        empirical = stats["wins"] / stats["count"]
        return max(0.0, min(1.0, raw * 0.6 + empirical * 0.4))


def build_decision(candidate: dict, price: float, stop: float, target: float, regime: str,
                   features: dict[str, Any], calibrator: ConfidenceCalibrator,
                   max_age_seconds: int = 90) -> SignalDecision:
    raw = float(candidate["score"])
    confidence = calibrator.adjust(candidate["setup"], raw)
    risk = abs(price - stop)
    reward = abs(target - price)
    net_r = reward / risk if risk else 0.0
    grade = "A" if confidence >= .78 and net_r >= 1.8 else "B" if confidence >= .65 and net_r >= 1.5 else "C"
    approved = grade == "A" and net_r >= 1.8
    return SignalDecision(approved, candidate["setup"], candidate["side"], grade, confidence, regime,
                          price, stop, target, datetime.now(timezone.utc) + timedelta(seconds=max_age_seconds),
                          net_r, tuple(candidate.get("reasons", [])), tuple(),
                          ("stop_broken", "data_stale", "regime_changed"), features)
