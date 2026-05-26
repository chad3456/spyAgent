"""
Fires Agent — global active wildfire detection.

Source: NASA FIRMS (Fire Information for Resource Management System).
- Public CSV endpoint, no key required for the 24h global VIIRS / MODIS feed.
- Falls back to GDELT wildfire news if FIRMS CSV is unreachable.

Returns up to MAX_FIRES active fire detections worldwide.
"""
from __future__ import annotations


import csv
import io
import logging
from datetime import datetime, timezone
from typing import Optional

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# NASA FIRMS public CSV — VIIRS S-NPP (375 m), 24 hour global, no auth required.
FIRMS_VIIRS_24H = (
    "https://firms.modaps.eosdis.nasa.gov/data/active_fire/"
    "noaa-20-viirs-c2/csv/J1_VIIRS_C2_Global_24h.csv"
)
FIRMS_MODIS_24H = (
    "https://firms.modaps.eosdis.nasa.gov/data/active_fire/"
    "modis-c6.1/csv/MODIS_C6_1_Global_24h.csv"
)

MAX_FIRES = 800
HIGH_CONFIDENCE_FRP = 50.0   # MW (fire radiative power)
CRITICAL_FRP = 200.0


def _severity(frp: float, confidence: Optional[str]) -> str:
    if frp >= CRITICAL_FRP:
        return "CRITICAL"
    if frp >= HIGH_CONFIDENCE_FRP:
        return "HIGH"
    if confidence in ("h", "high"):
        return "MEDIUM"
    return "LOW"


def _parse_firms_csv(text: str, sensor: str) -> list[dict]:
    fires: list[dict] = []
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        try:
            lat = float(row.get("latitude") or 0)
            lon = float(row.get("longitude") or 0)
            frp = float(row.get("frp") or 0)
            brightness = float(row.get("bright_ti4") or row.get("brightness") or 0)
        except (TypeError, ValueError):
            continue
        if lat == 0 and lon == 0:
            continue
        confidence = (row.get("confidence") or "").lower()
        acq_date = row.get("acq_date") or ""
        acq_time = row.get("acq_time") or ""
        fires.append({
            "id": f"{sensor}-{lat:.4f}-{lon:.4f}-{acq_date}{acq_time}",
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "brightness": round(brightness, 1),
            "frp": round(frp, 2),
            "confidence": confidence,
            "sensor": sensor,
            "acquired": f"{acq_date}T{acq_time[:2] or '00'}:{acq_time[2:4] or '00'}:00Z" if acq_date else "",
            "dayNight": (row.get("daynight") or "").upper(),
            "severity": _severity(frp, confidence),
        })
        if len(fires) >= MAX_FIRES:
            break
    return fires


class FiresAgent(BaseAgent):
    cache_prefix = "fires"

    async def fetch_data(self) -> dict:
        # Try VIIRS first (higher resolution), then MODIS as backup.
        for url, sensor in ((FIRMS_VIIRS_24H, "VIIRS"), (FIRMS_MODIS_24H, "MODIS")):
            text = await self.fetch_text(url, cache_key=f"fires:csv:{sensor}")
            if not text or "latitude" not in text[:200]:
                continue
            fires = _parse_firms_csv(text, sensor)
            if not fires:
                continue
            fires.sort(key=lambda f: f["frp"], reverse=True)
            summary = {
                "total": len(fires),
                "critical": sum(1 for f in fires if f["severity"] == "CRITICAL"),
                "high": sum(1 for f in fires if f["severity"] == "HIGH"),
                "source": sensor,
            }
            news = await self.fetch_gdelt(
                "wildfire OR \"forest fire\" OR bushfire", max_records=8, category="fires"
            )
            return {
                "fires": fires,
                "news": news,
                "summary": summary,
                "source": f"NASA FIRMS {sensor} 24h",
                "fetchedAt": datetime.now(timezone.utc).isoformat(),
            }

        # All FIRMS endpoints failed — fall back to news only.
        news = await self.fetch_gdelt(
            "wildfire OR \"forest fire\" OR bushfire", max_records=15, category="fires"
        )
        return {
            "fires": [],
            "news": news,
            "summary": {"total": 0, "critical": 0, "high": 0, "source": "news-only"},
            "source": "GDELT (FIRMS unreachable)",
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }
