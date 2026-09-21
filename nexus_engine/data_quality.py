from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .signal_models import DataQuality


class DataQualityGate:
    def __init__(self, max_age_ms: int = 15_000, min_candles: int = 80):
        self.max_age_ms = max_age_ms
        self.min_candles = min_candles

    def check(self, datasets: dict[str, Any]) -> DataQuality:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        missing: list[str] = []
        latest = 0
        for name, value in datasets.items():
            if value is None or value == [] or value == {}:
                missing.append(name)
                continue
            if name.endswith("_candles") and len(value) < self.min_candles:
                missing.append(f"{name}:insufficient_history")
            if isinstance(value, dict):
                event_time = value.get("E") or value.get("time") or value.get("serverTime")
                if event_time:
                    latest = max(latest, int(event_time))
        age = max(0, now - latest) if latest else self.max_age_ms + 1
        reasons = []
        if age > self.max_age_ms:
            reasons.append(f"stale_data:{age}ms")
        if missing:
            reasons.append("missing_or_incomplete_data")
        return DataQuality(not reasons, datetime.now(timezone.utc), latest, self.max_age_ms, tuple(missing), tuple(reasons))
