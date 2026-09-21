from __future__ import annotations

from dataclasses import dataclass

from .indicators import TimeframeFeatures


@dataclass(frozen=True)
class StructureAnalysis:
    bias: str
    alignment: float
    state: str
    support: float
    resistance: float
    swept_side: str | None


def analyze_structure(features: dict[str, TimeframeFeatures], candles_by_tf: dict[str, list]) -> StructureAnalysis:
    higher = [features[x].trend for x in ("12h", "8h", "4h") if x in features]
    medium = [features[x].trend for x in ("2h", "1h") if x in features]
    up = sum(x == "up" for x in higher + medium)
    down = sum(x == "down" for x in higher + medium)
    bias = "bullish" if up > down and up >= 3 else "bearish" if down > up and down >= 3 else "neutral"
    alignment = max(up, down) / max(1, len(higher) + len(medium))
    base = candles_by_tf.get("15m", [])
    recent = base[-40:]
    support = min((c.low for c in recent), default=0.0)
    resistance = max((c.high for c in recent), default=0.0)
    close = recent[-1].close if recent else 0.0
    swept = "sell_side_reclaimed" if recent and recent[-1].low < support and close > support else None
    state = "trend" if alignment >= 0.7 else "range" if bias == "neutral" else "transition"
    return StructureAnalysis(bias, alignment, state, support, resistance, swept)
