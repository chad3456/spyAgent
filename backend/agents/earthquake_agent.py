"""
Earthquake Agent — real-time seismic events from USGS Earthquake Hazards Program.

Fetches three feeds concurrently:
- Significant earthquakes (past 7 days)
- M4.5+ (past 7 days)
- M2.5+ (past day)

GeoJSON spec: https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php
"""

import asyncio
import logging
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

USGS_FEEDS = {
    "significant_week": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson",
    "m45_week": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson",
    "m25_day": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson",
}

ALERT_COLORS = {
    "green": "LOW",
    "yellow": "MEDIUM",
    "orange": "HIGH",
    "red": "CRITICAL",
}


def _severity(mag) -> str:
    if mag is None:
        return "INFO"
    if mag >= 7.0:
        return "CRITICAL"
    if mag >= 6.0:
        return "HIGH"
    if mag >= 5.0:
        return "MEDIUM"
    if mag >= 4.0:
        return "LOW"
    return "INFO"


def _parse_feature(feature: dict) -> dict | None:
    """Convert a GeoJSON Feature to a normalised earthquake dict."""
    try:
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        coords = geom.get("coordinates", [])
        if not coords or len(coords) < 3:
            return None

        lon, lat, depth = coords[0], coords[1], coords[2]
        if lat is None or lon is None:
            return None

        mag = props.get("mag")
        time_ms = props.get("time")
        event_time = (
            datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc).isoformat()
            if time_ms
            else None
        )

        alert_raw = (props.get("alert") or "").lower()
        alert = ALERT_COLORS.get(alert_raw, alert_raw.upper() if alert_raw else None)

        return {
            "id": feature.get("id") or props.get("code", ""),
            "magnitude": round(mag, 1) if mag is not None else None,
            "place": props.get("place", ""),
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "depth": round(depth, 1) if depth is not None else None,
            "time": event_time,
            "alert": alert,
            "tsunami": bool(props.get("tsunami")),
            "url": props.get("url", ""),
            "severity": _severity(mag),
            "felt": props.get("felt"),
            "sig": props.get("sig"),
            "magType": props.get("magType", ""),
            "status": props.get("status", ""),
        }
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to parse earthquake feature: %s", exc)
        return None


class EarthquakeAgent(BaseAgent):
    cache_prefix = "earthquakes"

    async def _fetch_feed(self, feed_name: str, url: str) -> list[dict]:
        data = await self.fetch_json(url, cache_key=f"{self.cache_prefix}:{feed_name}")
        if not data or not isinstance(data, dict):
            return []
        features = data.get("features") or []
        events = []
        for f in features:
            parsed = _parse_feature(f)
            if parsed:
                events.append(parsed)
        return events

    async def fetch_data(self) -> dict:
        cache_key = f"{self.cache_prefix}:all"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch all three feeds concurrently
        feed_results = await asyncio.gather(
            *[self._fetch_feed(name, url) for name, url in USGS_FEEDS.items()],
            return_exceptions=True,
        )

        # Merge and deduplicate by event id
        seen_ids: set[str] = set()
        all_events: list[dict] = []

        for batch in feed_results:
            if isinstance(batch, Exception):
                logger.warning("EarthquakeAgent feed error: %s", batch)
                continue
            for event in batch:
                eid = event.get("id", "")
                if eid and eid in seen_ids:
                    continue
                if eid:
                    seen_ids.add(eid)
                all_events.append(event)

        # Sort most recent first
        all_events.sort(key=lambda e: e.get("time") or "", reverse=True)

        # Augment with GDELT if no events returned
        gdelt_articles = []
        if not all_events:
            gdelt_articles = await self.fetch_gdelt(
                query="earthquake disaster seismic",
                max_records=10,
                category="earthquake",
            )

        # Summary counts
        critical = sum(1 for e in all_events if e["severity"] == "CRITICAL")
        high = sum(1 for e in all_events if e["severity"] == "HIGH")
        tsunami_events = sum(1 for e in all_events if e.get("tsunami"))

        result = {
            "events": all_events,
            "total": len(all_events),
            "summary": {
                "total": len(all_events),
                "critical": critical,
                "high": high,
                "tsunamiAlerts": tsunami_events,
            },
            "gdeltArticles": gdelt_articles,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

        self._cache[cache_key] = result
        return result
