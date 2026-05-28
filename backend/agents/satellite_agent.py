"""
Satellite Agent — live positions of curated well-known satellites.

Strategy (avoids rate-limit issues):
  1. Fetch TLE data for each satellite from N2YO (if N2YO_API_KEY set)
     → TLEs are cached for 1 hour (only ~30 requests/hour for 30 satellites)
  2. Propagate TLE to current UTC time using sgp4 locally
     → zero API calls for position computation, instant and accurate
  3. Fallback: Celestrak bulk TLE files + sgp4 if N2YO key not set

Curated list: 30 most-tracked / best-known satellites across all categories
(Space Stations, Earth Observation, Weather, Navigation, Communications,
Military, Commercial Imaging, Science).

Required env var (free registration at https://www.n2yo.com/api/):
  N2YO_API_KEY=xxxxxx-xxxxxx-xxxxxx-xxxxxx

Without the key the agent falls back to Celestrak bulk TLE feeds.
"""
from __future__ import annotations


import asyncio
import logging
import math
import os
from cachetools import TTLCache
from datetime import datetime, timezone

import httpx

from .base_agent import BaseAgent, _HEADERS

logger = logging.getLogger(__name__)

# ─── N2YO endpoints ───────────────────────────────────────────────────────────
N2YO_TLE_URL = "https://api.n2yo.com/rest/v1/satellite/tle/{norad_id}&apiKey={key}"

# ─── Celestrak bulk TLE fallback ─────────────────────────────────────────────
CELESTRAK_FEEDS = {
    "stations":  "https://celestrak.org/pub/TLE/stations.txt",
    "weather":   "https://celestrak.org/pub/TLE/weather.txt",
    "gps":       "https://celestrak.org/pub/TLE/gps-ops.txt",
    "earthobs":  "https://celestrak.org/pub/TLE/eo-satml.txt",
}

# ─── TLE cache (TTL 1 hour — TLEs rarely change more than twice daily) ────────
_tle_cache: TTLCache = TTLCache(maxsize=128, ttl=3600)

# ─── Curated satellite list ───────────────────────────────────────────────────
# (norad_id, display_name, category, description, country/agency)
CURATED_SATELLITES: list[tuple[int, str, str, str, str]] = [
    # ── Space Stations ────────────────────────────────────────────────────────
    (25544, "ISS",             "Space Station",    "International Space Station",         "USA/International"),
    (48274, "CSS (Tiangong)",  "Space Station",    "Chinese Space Station — Tianhe core", "China"),

    # ── Earth Observation ─────────────────────────────────────────────────────
    (20580, "Hubble",          "Science",          "Hubble Space Telescope",              "USA (NASA)"),
    (39634, "Sentinel-1A",     "Earth Observation","ESA SAR all-weather imaging",         "Europe (ESA)"),
    (40697, "Sentinel-2A",     "Earth Observation","ESA multispectral land monitoring",   "Europe (ESA)"),
    (42063, "Sentinel-2B",     "Earth Observation","ESA multispectral land monitoring",   "Europe (ESA)"),
    (44493, "Sentinel-6A",     "Earth Observation","ESA/NOAA ocean surface topography",  "Europe/USA"),
    (39084, "Landsat-8",       "Earth Observation","NASA/USGS land imaging",              "USA (NASA)"),
    (49260, "Landsat-9",       "Earth Observation","NASA/USGS land imaging",              "USA (NASA)"),
    (25994, "Terra (EOS AM-1)","Earth Observation","NASA multispectral earth science",    "USA (NASA)"),
    (27424, "Aqua (EOS PM-1)", "Earth Observation","NASA atmospheric & ocean science",    "USA (NASA)"),
    (36508, "CryoSat-2",       "Science",          "ESA ice thickness measurement",       "Europe (ESA)"),
    (41240, "Jason-3",         "Science",          "NOAA/EUMETSAT ocean topography",      "USA/Europe"),
    (43476, "GRACE-FO 1",      "Science",          "NASA/DLR gravity field mapping",      "USA/Germany"),

    # ── Weather / Meteorology ─────────────────────────────────────────────────
    (33591, "NOAA-19",         "Weather",          "NOAA polar-orbit weather (last POES)","USA (NOAA)"),
    (43013, "NOAA-20 (JPSS-1)","Weather",          "NOAA Joint Polar Satellite System",   "USA (NOAA)"),
    (37849, "Suomi NPP",       "Weather",          "NOAA/NASA Suomi National Polar-orbit","USA"),
    (41866, "GOES-16",         "Weather",          "NOAA geostationary weather — East",   "USA (NOAA)"),
    (43226, "GOES-17",         "Weather",          "NOAA geostationary weather — West",   "USA (NOAA)"),
    (51850, "GOES-18",         "Weather",          "NOAA geostationary weather — West",   "USA (NOAA)"),
    (38552, "Meteosat-11",     "Weather",          "EUMETSAT geostationary weather",      "Europe"),
    (40069, "Himawari-8",      "Weather",          "JMA geostationary weather — Pacific", "Japan"),

    # ── Navigation ───────────────────────────────────────────────────────────
    (28474, "GPS BIIRM-1",     "Navigation",       "US GPS Block IIR-M satellite",        "USA (DoD)"),
    (36585, "GPS BIIF-1",      "Navigation",       "US GPS Block IIF satellite",           "USA (DoD)"),
    (44506, "GPS BIII-3",      "Navigation",       "US GPS Block III — Cosmos",            "USA (DoD)"),

    # ── Communications ────────────────────────────────────────────────────────
    (41917, "Iridium NEXT-1",  "Communications",   "Iridium LEO communications network",  "USA"),
    (44713, "Starlink-1007",   "Communications",   "SpaceX Starlink broadband LEO",       "USA (SpaceX)"),
    (44714, "Starlink-1008",   "Communications",   "SpaceX Starlink broadband LEO",       "USA (SpaceX)"),

    # ── Commercial Imaging ────────────────────────────────────────────────────
    (33331, "GeoEye-1",        "Commercial",       "Maxar high-resolution earth imaging", "USA"),
    (40115, "WorldView-3",     "Commercial",       "Maxar 31cm sub-metre imaging",        "USA"),

    # ── Military ──────────────────────────────────────────────────────────────
    (43874, "WGS-10",          "Military",         "US Wideband Global SATCOM",           "USA (DoD)"),
    (44235, "GPS BIII-2",      "Military",         "US GPS Block III — Magellan",          "USA (DoD)"),
]


# ─── SGP4 helpers ─────────────────────────────────────────────────────────────

def _teme_to_geodetic(x_km: float, y_km: float, z_km: float) -> tuple[float, float, float]:
    """TEME XYZ → geodetic (lat, lon, altitude_km). Spherical approximation."""
    lon = math.degrees(math.atan2(y_km, x_km))
    r = math.sqrt(x_km ** 2 + y_km ** 2 + z_km ** 2)
    lat = math.degrees(math.asin(z_km / r)) if r > 0 else 0.0
    alt = r - 6371.0
    return round(lat, 4), round(lon, 4), round(alt, 1)


def _parse_tle_from_n2yo(tle_field: str) -> tuple[str, str] | None:
    """Parse N2YO's 'tle' field which contains line1\r\nline2."""
    try:
        parts = tle_field.strip().replace("\r\n", "\n").replace("\r", "\n").split("\n")
        parts = [p.strip() for p in parts if p.strip()]
        for i, p in enumerate(parts):
            if p.startswith("1 ") and i + 1 < len(parts) and parts[i + 1].startswith("2 "):
                return parts[i], parts[i + 1]
    except Exception:
        pass
    return None


def _parse_tle_blocks(text: str) -> dict[int, tuple[str, str, str]]:
    """Parse bulk TLE text → {norad_id: (name, line1, line2)}."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    result: dict[int, tuple[str, str, str]] = {}
    i = 0
    while i < len(lines):
        if (
            not lines[i].startswith("1 ")
            and not lines[i].startswith("2 ")
            and i + 2 < len(lines)
            and lines[i + 1].startswith("1 ")
            and lines[i + 2].startswith("2 ")
        ):
            name = lines[i]
            l1, l2 = lines[i + 1], lines[i + 2]
            try:
                norad_id = int(l2.split()[1])
                result[norad_id] = (name, l1, l2)
            except (ValueError, IndexError):
                pass
            i += 3
        else:
            i += 1
    return result


def _propagate_tle(name: str, line1: str, line2: str) -> dict | None:
    """Propagate TLE to current UTC time using sgp4. Returns position dict or None."""
    try:
        from sgp4.api import Satrec, jday as sgp4_jday
    except ImportError:
        return None

    try:
        sat = Satrec.twoline2rv(line1, line2)
        now = datetime.now(timezone.utc)
        jd, fr = sgp4_jday(
            now.year, now.month, now.day,
            now.hour, now.minute,
            now.second + now.microsecond / 1_000_000,
        )
        e, r, v = sat.sgp4(jd, fr)
        if e != 0 or not r:
            return None

        lat, lon, alt = _teme_to_geodetic(*r)
        if alt < -100 or alt > 60_000:
            return None

        speed_kms = round(math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2), 3) if v else None
        speed_kmh = round(speed_kms * 3600, 0) if speed_kms else None

        try:
            inclination = float(line2[8:16].strip())
            mean_motion = float(line2[52:63].strip())
            period_min = round(1440.0 / mean_motion, 2) if mean_motion else None
        except (ValueError, IndexError):
            inclination, period_min = None, None

        return {
            "lat": lat,
            "lon": lon,
            "altitude": alt,
            "velocity_kms": speed_kms,
            "velocity_kmh": speed_kmh,
            "inclination": inclination,
            "period_min": period_min,
            "noradId": sat.satnum,
        }
    except Exception as exc:
        logger.debug("sgp4 error for %s: %s", name, exc)
        return None


# ─── Main Agent ───────────────────────────────────────────────────────────────

class SatelliteAgent(BaseAgent):
    cache_prefix = "satellites"

    def __init__(self, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self._n2yo_key: str | None = os.getenv("N2YO_API_KEY", "").strip() or None
        # Separate long-lived TLE cache (1 hour TTL)
        self._tle_store: TTLCache = _tle_cache

    # ── N2YO TLE fetch ────────────────────────────────────────────────────────

    async def _fetch_n2yo_tle(self, norad_id: int) -> tuple[str, str] | None:
        """Fetch TLE lines from N2YO for a single satellite. Cached 1 hour."""
        if not self._n2yo_key:
            return None

        tle_key = f"n2yo:tle:{norad_id}"
        if tle_key in self._tle_store:
            return self._tle_store[tle_key]

        url = N2YO_TLE_URL.format(norad_id=norad_id, key=self._n2yo_key)
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers=_HEADERS) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    tle_field = data.get("tle", "")
                    parsed = _parse_tle_from_n2yo(tle_field)
                    if parsed:
                        self._tle_store[tle_key] = parsed
                        return parsed
                else:
                    logger.warning("N2YO TLE %d: HTTP %d", norad_id, resp.status_code)
        except Exception as exc:
            logger.info("N2YO TLE %d failed: %s", norad_id, exc)
        return None

    # ── Celestrak bulk fallback ────────────────────────────────────────────────

    async def _fetch_celestrak_tles(self) -> dict[int, tuple[str, str, str]]:
        """Fetch bulk TLE files from Celestrak and return a NORAD-keyed dict."""
        ck = "celestrak:bulk"
        if ck in self._tle_store:
            return self._tle_store[ck]

        combined: dict[int, tuple[str, str, str]] = {}
        tasks = [self.fetch_text(url, cache_key=f"tle:{name}") for name, url in CELESTRAK_FEEDS.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for text in results:
            if isinstance(text, Exception) or not text:
                continue
            combined.update(_parse_tle_blocks(text))

        self._tle_store[ck] = combined
        return combined

    # ── Build satellite record ────────────────────────────────────────────────

    def _build_record(
        self,
        norad_id: int,
        display_name: str,
        category: str,
        description: str,
        agency: str,
        line1: str,
        line2: str,
    ) -> dict | None:
        pos = _propagate_tle(display_name, line1, line2)
        if not pos:
            return None
        return {
            "noradId":     norad_id,
            "name":        display_name,
            "category":    category,
            "description": description,
            "agency":      agency,
            "lat":         pos["lat"],
            "lon":         pos["lon"],
            "altitude":    pos["altitude"],
            "velocity_kms": pos.get("velocity_kms"),
            "velocity_kmh": pos.get("velocity_kmh"),
            "inclination": pos.get("inclination"),
            "period_min":  pos.get("period_min"),
            "source":      "n2yo+sgp4" if self._n2yo_key else "celestrak+sgp4",
            # Orbit type based on altitude
            "orbitType":   _orbit_type(pos["altitude"]),
        }

    # ── Main fetch ────────────────────────────────────────────────────────────

    async def fetch_data(self) -> dict:
        # Positions change every second — cache for 60s only
        pos_cache_key = f"{self.cache_prefix}:positions"
        cached = self._cache.get(pos_cache_key)
        if cached is not None:
            return cached

        # Verify sgp4 available
        try:
            import sgp4.api  # noqa: F401
        except ImportError:
            return {
                "satellites": [],
                "total": 0,
                "error": "sgp4 not installed — run: pip install sgp4",
                "fetchedAt": datetime.now(timezone.utc).isoformat(),
            }

        satellites: list[dict] = []

        if self._n2yo_key:
            # ── Path A: N2YO TLE (cached 1h) + local sgp4 ────────────────────
            logger.info("SatelliteAgent: using N2YO TLE source (%d satellites)", len(CURATED_SATELLITES))

            tle_tasks = [
                self._fetch_n2yo_tle(norad_id)
                for norad_id, *_ in CURATED_SATELLITES
            ]
            tle_results = await asyncio.gather(*tle_tasks, return_exceptions=True)

            for (norad_id, name, cat, desc, agency), tle in zip(CURATED_SATELLITES, tle_results):
                if isinstance(tle, Exception) or not tle:
                    continue
                line1, line2 = tle
                rec = self._build_record(norad_id, name, cat, desc, agency, line1, line2)
                if rec:
                    satellites.append(rec)

        else:
            # ── Path B: Celestrak bulk TLE + sgp4 ────────────────────────────
            logger.info("SatelliteAgent: N2YO key not set, using Celestrak fallback")
            bulk = await self._fetch_celestrak_tles()

            for norad_id, name, cat, desc, agency in CURATED_SATELLITES:
                entry = bulk.get(norad_id)
                if not entry:
                    # Try by name match
                    for nid, (bname, l1, l2) in bulk.items():
                        if name.upper().split("(")[0].strip() in bname.upper():
                            entry = (bname, l1, l2)
                            norad_id = nid
                            break
                if not entry:
                    logger.debug("No TLE found for %s (NORAD %d)", name, norad_id)
                    continue
                _, line1, line2 = entry
                rec = self._build_record(norad_id, name, cat, desc, agency, line1, line2)
                if rec:
                    satellites.append(rec)

        # Summarise by category
        by_cat: dict[str, int] = {}
        for s in satellites:
            by_cat[s["category"]] = by_cat.get(s["category"], 0) + 1

        result = {
            "satellites":  satellites,
            "total":       len(satellites),
            "categories":  by_cat,
            "source":      "n2yo+sgp4" if self._n2yo_key else "celestrak+sgp4",
            "n2yoEnabled": bool(self._n2yo_key),
            "fetchedAt":   datetime.now(timezone.utc).isoformat(),
        }

        if satellites:
            self._cache[pos_cache_key] = result

        logger.info("SatelliteAgent: returning %d satellites (source=%s)", len(satellites), result["source"])
        return result


def _orbit_type(alt_km: float) -> str:
    """Classify orbit by altitude."""
    if alt_km < 2000:
        return "LEO"    # Low Earth Orbit
    if alt_km < 20200:
        return "MEO"    # Medium Earth Orbit
    if 35586 < alt_km < 35986:
        return "GEO"    # Geostationary Orbit
    if alt_km >= 35986:
        return "HEO"    # High Earth Orbit
    return "MEO"
