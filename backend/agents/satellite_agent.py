"""
Satellite Agent — live orbital positions of active satellites.

Sources (Celestrak, free, no auth):
- Space stations:    https://celestrak.org/pub/TLE/stations.txt
- Weather:           https://celestrak.org/pub/TLE/weather.txt
- GPS (active):      https://celestrak.org/pub/TLE/gps-ops.txt
- Earth observation: https://celestrak.org/pub/TLE/eo-satml.txt
- Amateur:           https://celestrak.org/pub/TLE/amateur.txt

TLE data is propagated to current time using the sgp4 library.
Positions are returned in geodetic lat/lon/altitude.

Returns up to 200 satellites with:
  {name, noradId, lat, lon, altitude, velocity, inclination, period, type, category}
"""

import asyncio
import logging
import math
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

CELESTRAK_FEEDS: list[tuple[str, str]] = [
    ("https://celestrak.org/pub/TLE/stations.txt", "Station"),
    ("https://celestrak.org/pub/TLE/weather.txt", "Weather"),
    ("https://celestrak.org/pub/TLE/gps-ops.txt", "GPS"),
    ("https://celestrak.org/pub/TLE/eo-satml.txt", "EarthObservation"),
    ("https://celestrak.org/pub/TLE/amateur.txt", "Amateur"),
]

MAX_SATELLITES = 200
MAX_PER_CATEGORY = 60  # cap per feed to keep total ≤ 200


def _teme_to_geodetic(x_km: float, y_km: float, z_km: float) -> tuple[float, float, float]:
    """
    Convert TEME (True Equator Mean Equinox) Cartesian coordinates to
    approximate geodetic latitude, longitude, altitude.

    This is a spherical approximation; errors < ~0.1° for LEO satellites.
    """
    lon = math.degrees(math.atan2(y_km, x_km))
    r = math.sqrt(x_km ** 2 + y_km ** 2 + z_km ** 2)
    lat = math.degrees(math.asin(z_km / r)) if r > 0 else 0.0
    alt = r - 6371.0  # subtract Earth's mean radius (km)
    return round(lat, 4), round(lon, 4), round(alt, 1)


def _parse_tle_blocks(text: str) -> list[tuple[str, str, str]]:
    """
    Parse a TLE file into (name, line1, line2) triples.
    Handles both 2-line and 3-line (name + 2 TLE lines) formats.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    triples: list[tuple[str, str, str]] = []
    i = 0
    while i < len(lines):
        # Look for a name line followed by two TLE lines
        if (
            not lines[i].startswith("1 ")
            and not lines[i].startswith("2 ")
            and i + 2 < len(lines)
            and lines[i + 1].startswith("1 ")
            and lines[i + 2].startswith("2 ")
        ):
            triples.append((lines[i], lines[i + 1], lines[i + 2]))
            i += 3
        elif (
            lines[i].startswith("1 ")
            and i + 1 < len(lines)
            and lines[i + 1].startswith("2 ")
        ):
            # Nameless TLE pair — use NORAD ID as name
            norad = lines[i].split()[1].rstrip("U")
            triples.append((f"SAT-{norad}", lines[i], lines[i + 1]))
            i += 2
        else:
            i += 1
    return triples


def _propagate(name: str, line1: str, line2: str, jd: float, fr: float, category: str) -> dict | None:
    """
    Propagate TLE to (jd, fr) using sgp4 and return a satellite record or None on error.
    """
    try:
        from sgp4.api import Satrec, jday as sgp4_jday  # noqa: F401
    except ImportError:
        return None

    try:
        sat = Satrec.twoline2rv(line1, line2)
        e, r, v = sat.sgp4(jd, fr)

        if e != 0 or not r:
            return None

        lat, lon, alt = _teme_to_geodetic(*r)

        # Skip satellites below the surface or way too high (bad TLE)
        if alt < -100 or alt > 60_000:
            return None

        # Velocity magnitude (km/s)
        speed = round(math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2), 3) if v else None

        # Inclination and period from mean motion (rev/day) stored in TLE line 2
        try:
            inclination = float(line2[8:16].strip())
            mean_motion_rev_day = float(line2[52:63].strip())
            period_min = round(1440.0 / mean_motion_rev_day, 2) if mean_motion_rev_day else None
        except (ValueError, IndexError):
            inclination = None
            period_min = None

        norad_id = sat.satnum

        return {
            "name": name.strip(),
            "noradId": norad_id,
            "lat": lat,
            "lon": lon,
            "altitude": alt,
            "velocity": speed,
            "inclination": inclination,
            "period": period_min,
            "category": category,
            "type": _classify_satellite(name, category),
        }
    except Exception as exc:  # noqa: BLE001
        logger.debug("sgp4 propagation failed for %s: %s", name, exc)
        return None


def _classify_satellite(name: str, category: str) -> str:
    """Map name/category to a human-readable type string."""
    upper = name.upper()
    if category == "Station":
        return "Space Station"
    if category == "GPS":
        return "Navigation"
    if category == "Weather":
        return "Weather"
    if category == "EarthObservation":
        return "Earth Observation"
    if category == "Amateur":
        return "Amateur"
    if any(k in upper for k in ("ISS", "TIANGONG", "ZARYA", "MIR", "CSS")):
        return "Space Station"
    if any(k in upper for k in ("NOAA", "METOP", "GOES", "METEOR", "FENG")):
        return "Weather"
    if any(k in upper for k in ("GPS", "NAVSTAR", "GLONASS", "GALILEO", "BEIDOU")):
        return "Navigation"
    return "Other"


class SatelliteAgent(BaseAgent):
    cache_prefix = "satellites"

    async def _fetch_category(self, url: str, category: str) -> list[dict]:
        text = await self.fetch_text(url, cache_key=f"{self.cache_prefix}:tle:{category}")
        if not text:
            return []

        triples = _parse_tle_blocks(text)

        # Compute Julian date once for current UTC time
        try:
            from sgp4.api import jday as sgp4_jday
        except ImportError:
            logger.error("sgp4 library not installed. Run: pip install sgp4")
            return []

        now = datetime.now(timezone.utc)
        jd, fr = sgp4_jday(
            now.year, now.month, now.day,
            now.hour, now.minute,
            now.second + now.microsecond / 1_000_000,
        )

        satellites: list[dict] = []
        for name, line1, line2 in triples[:MAX_PER_CATEGORY]:
            record = _propagate(name, line1, line2, jd, fr, category)
            if record:
                satellites.append(record)

        return satellites

    async def fetch_data(self) -> dict:
        cache_key = f"{self.cache_prefix}:all"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        # Verify sgp4 is available before making network requests
        try:
            import sgp4.api  # noqa: F401
        except ImportError:
            logger.error("sgp4 not installed. Install with: pip install sgp4")
            result = {
                "satellites": [],
                "total": 0,
                "error": "sgp4 library not installed",
                "fetchedAt": datetime.now(timezone.utc).isoformat(),
            }
            return result

        tasks = [
            self._fetch_category(url, category)
            for url, category in CELESTRAK_FEEDS
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_sats: list[dict] = []
        seen_norad: set[int] = set()

        for batch in results:
            if isinstance(batch, Exception):
                logger.warning("SatelliteAgent feed error: %s", batch)
                continue
            for sat in batch:
                nid = sat.get("noradId")
                if nid in seen_norad:
                    continue
                if nid:
                    seen_norad.add(nid)
                all_sats.append(sat)
                if len(all_sats) >= MAX_SATELLITES:
                    break
            if len(all_sats) >= MAX_SATELLITES:
                break

        # Summary by category
        category_counts: dict[str, int] = {}
        for s in all_sats:
            cat = s.get("category", "Other")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        result = {
            "satellites": all_sats,
            "total": len(all_sats),
            "categories": category_counts,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

        self._cache[cache_key] = result
        return result
