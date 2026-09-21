from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class DataQuality:
    ok: bool
    checked_at: datetime
    latest_event_ms: int
    max_age_ms: int
    missing: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class LiquidityMap:
    support: float
    resistance: float
    nearest_support_distance: float
    nearest_resistance_distance: float
    room_for_long: bool
    room_for_short: bool
    swept_side: Optional[str] = None


@dataclass(frozen=True)
class OrderFlowPersistence:
    current_imbalance: float
    rolling_imbalance: float
    persistence: float
    absorption: str
    exhaustion: bool


@dataclass(frozen=True)
class SignalDecision:
    approved: bool
    setup: str
    side: str
    grade: str
    confidence: float
    regime: str
    entry: float
    stop: float
    target: float
    expires_at: datetime
    expected_net_r: float
    reasons: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    invalidations: tuple[str, ...] = field(default_factory=tuple)
    feature_snapshot: dict[str, Any] = field(default_factory=dict)

    @property
    def live_eligible(self) -> bool:
        return self.approved and self.grade == "A" and datetime.now(timezone.utc) < self.expires_at
