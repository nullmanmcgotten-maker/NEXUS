from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .market_math import normalize_klines


class DataQualityGate:
    def __init__(self, max_age_ms: int = 15_000, min_candles: int = 80):
        self.max_age_ms = max_age_ms
        self.min_candles = min_candles

    def _latest_timestamp(self, name: str, value: Any) -> int:
        if name.endswith("_candles") and value:
            candles = normalize_klines(value)
            return candles[-1].close_time if candles else 0
        if isinstance(value, list) and value:
            times = [int(x.get("T") or x.get("time") or x.get("E") or 0) for x in value if isinstance(x, dict)]
            return max(times, default=0)
        if isinstance(value, dict):
            return int(value.get("time") or value.get("E") or value.get("T") or 0)
        return 0

    def check(self, datasets: dict[str, Any]) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        missing: list[str] = []
        timestamps: list[int] = []
        for name, value in datasets.items():
            if value is None or value == [] or value == {}:
                missing.append(name)
                continue
            if name.endswith("_candles"):
                candles = normalize_klines(value)
                if len(candles) < self.min_candles:
                    missing.append(f"{name}:insufficient_history")
            timestamp = self._latest_timestamp(name, value)
            if timestamp:
                timestamps.append(timestamp)
        latest = min(timestamps) if timestamps else 0
        age = now - latest if latest else self.max_age_ms + 1
        reasons: list[str] = []
        if age > self.max_age_ms:
            reasons.append(f"stale_data:{age}ms")
        if missing:
            reasons.append("missing_or_incomplete_data")
        return {"ok": not reasons, "latest_event_ms": latest, "age_ms": max(age, 0), "missing": missing, "reasons": reasons}
