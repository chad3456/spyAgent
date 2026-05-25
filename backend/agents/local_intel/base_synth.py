"""
Shared utilities for the local intel synthesizers.
"""

import math
from datetime import datetime, timezone
from typing import Optional


# Country bounding boxes (lat_min, lat_max, lon_min, lon_max). Approximate —
# good enough to decide "is this lat/lon roughly inside country X".
COUNTRY_BBOX: dict[str, tuple[float, float, float, float]] = {
    "US": (24.5, 49.4, -125.0, -66.9),
    "RU": (41.2, 81.9, 19.6, 180.0),
    "CN": (18.2, 53.6, 73.6, 134.8),
    "IN": (6.5, 35.7, 68.1, 97.4),
    "IR": (25.0, 39.8, 44.0, 63.4),
    "IL": (29.5, 33.4, 34.3, 35.9),
    "UA": (44.4, 52.4, 22.1, 40.2),
    "PK": (23.5, 37.1, 60.9, 77.0),
    "YE": (12.1, 19.0, 41.8, 54.5),
    "SY": (32.3, 37.3, 35.7, 42.4),
    "IQ": (29.1, 37.4, 38.8, 48.6),
    "AF": (29.4, 38.5, 60.5, 74.9),
    "TW": (21.9, 25.3, 119.3, 122.0),
    "JP": (24.0, 45.5, 122.9, 145.8),
    "KR": (33.1, 38.6, 125.1, 129.6),
    "GB": (49.9, 60.9, -8.6, 1.8),
    "FR": (41.3, 51.1, -5.1, 9.6),
    "DE": (47.3, 55.1, 5.9, 15.0),
}


def country_bbox(cc: str) -> Optional[tuple[float, float, float, float]]:
    return COUNTRY_BBOX.get(cc.upper())


def in_country(lat: float, lon: float, cc: str) -> bool:
    bb = country_bbox(cc)
    if not bb:
        return False
    lat_min, lat_max, lon_min, lon_max = bb
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometres."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlamb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlamb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# Severity score for ranking — higher = more acute.
SEVERITY_WEIGHTS: dict[str, int] = {
    "CRITICAL": 100,
    "HIGH": 60,
    "MEDIUM": 30,
    "LOW": 10,
    "INFO": 1,
    "BASELINE": 1,
}


def severity_score(value: str) -> int:
    return SEVERITY_WEIGHTS.get((value or "").upper(), 5)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BaseSynth:
    """Common base. Subclasses set `name` and implement `synthesise(raw)`."""

    name: str = "local_synth"

    def synthesise(self, raw: dict) -> dict:
        raise NotImplementedError

    def envelope(self, analysis: dict, model: str = "local-heuristic-v1") -> dict:
        return {
            "analyst": self.name,
            "model": model,
            "stopReason": "rules",
            "usage": {
                "inputTokens": 0,
                "outputTokens": 0,
                "cacheReadInputTokens": 0,
                "cacheCreationInputTokens": 0,
            },
            "analysis": analysis,
        }
