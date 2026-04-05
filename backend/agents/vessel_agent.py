"""
Vessel Agent — real-time AIS vessel tracking.

Source priority:
1. Datalastic API (free demo key gives a sample of vessels)
2. VesselFinder public endpoint
3. MyShipTracking public JSON endpoint
4. GDELT maritime news as final fallback (no position data, articles only)

Returns normalised vessel records:
  {mmsi, name, type, lat, lon, speed, heading, destination, flag, shipType}
"""

import asyncio
import logging
import os
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

DATALASTIC_URL = "https://api.datalastic.com/api/v0/vessel_find"
DATALASTIC_DEMO_KEY = "demo"

# Ship type codes → human-readable (ITU/AIS standard)
SHIP_TYPE_MAP = {
    0: "Unknown",
    20: "WIG",
    30: "Fishing",
    31: "Towing",
    32: "Towing Large",
    33: "Dredging",
    34: "Diving",
    35: "Military",
    36: "Sailing",
    37: "Pleasure Craft",
    40: "High-Speed Craft",
    50: "Pilot Vessel",
    51: "SAR",
    52: "Tug",
    53: "Port Tender",
    54: "Anti-Pollution",
    55: "Law Enforcement",
    58: "Medical Transport",
    60: "Passenger",
    70: "Cargo",
    71: "Cargo",
    72: "Cargo",
    80: "Tanker",
    81: "Tanker",
    82: "Tanker",
    89: "Tanker",
    90: "Other",
}


def _ship_type_label(type_code) -> str:
    if type_code is None:
        return "Unknown"
    try:
        code = int(type_code)
    except (ValueError, TypeError):
        return str(type_code)
    # Check exact match first, then decade bucket
    if code in SHIP_TYPE_MAP:
        return SHIP_TYPE_MAP[code]
    decade = (code // 10) * 10
    return SHIP_TYPE_MAP.get(decade, "Other")


class VesselAgent(BaseAgent):
    cache_prefix = "vessels"

    # ------------------------------------------------------------------
    # Source 1: Datalastic demo
    # ------------------------------------------------------------------
    async def _fetch_datalastic(self) -> list[dict]:
        """
        Datalastic /vessel_find endpoint.
        Demo key returns a limited sample of vessel records.
        """
        params = {
            "api-key": os.getenv("DATALASTIC_API_KEY", DATALASTIC_DEMO_KEY),
            "latitude": "0",
            "longitude": "0",
            "radius": "5000",  # km — very large to get global sample
        }
        data = await self.fetch_json(
            DATALASTIC_URL,
            params=params,
            cache_key=f"{self.cache_prefix}:datalastic",
        )
        vessels: list[dict] = []
        if not data:
            return vessels

        records = []
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            records = data.get("data", data.get("vessels", data.get("result", [])))

        for v in records:
            if not isinstance(v, dict):
                continue
            lat = v.get("lat") or v.get("latitude")
            lon = v.get("lon") or v.get("longitude")
            if lat is None or lon is None:
                continue
            try:
                lat, lon = float(lat), float(lon)
            except (ValueError, TypeError):
                continue

            vessels.append(
                {
                    "mmsi": str(v.get("mmsi", "")),
                    "name": (v.get("name") or v.get("ship_name") or "Unknown").strip(),
                    "type": _ship_type_label(v.get("ship_type") or v.get("type")),
                    "lat": round(lat, 5),
                    "lon": round(lon, 5),
                    "speed": v.get("speed") or v.get("sog"),
                    "heading": v.get("heading") or v.get("cog"),
                    "destination": (v.get("destination") or "").strip() or None,
                    "flag": v.get("flag") or v.get("country_iso"),
                    "shipType": _ship_type_label(v.get("ship_type") or v.get("type")),
                    "source": "datalastic",
                }
            )
        return vessels

    # ------------------------------------------------------------------
    # Source 2: VesselFinder public vessel list
    # ------------------------------------------------------------------
    async def _fetch_vesselfinder(self) -> list[dict]:
        """
        VesselFinder exposes a public JSON for the map view.
        Note: this is a best-effort scrape of their public endpoint.
        """
        url = "https://www.vesselfinder.com/api/pub/vesselsonmap"
        params = {
            "bbox": "-180,-85,180,85",
            "zoom": "2",
        }
        data = await self.fetch_json(
            url,
            params=params,
            cache_key=f"{self.cache_prefix}:vesselfinder",
        )
        vessels: list[dict] = []
        if not data:
            return vessels

        records = data if isinstance(data, list) else data.get("vessels", [])
        for v in records:
            if not isinstance(v, (list, dict)):
                continue
            # VesselFinder sometimes returns arrays: [mmsi, lat, lon, heading, speed, name, type]
            if isinstance(v, list) and len(v) >= 5:
                try:
                    lat, lon = float(v[1]), float(v[2])
                    vessels.append(
                        {
                            "mmsi": str(v[0]),
                            "name": str(v[5]) if len(v) > 5 else "Unknown",
                            "type": _ship_type_label(v[6] if len(v) > 6 else None),
                            "lat": round(lat, 5),
                            "lon": round(lon, 5),
                            "speed": v[4],
                            "heading": v[3],
                            "destination": None,
                            "flag": None,
                            "shipType": _ship_type_label(v[6] if len(v) > 6 else None),
                            "source": "vesselfinder",
                        }
                    )
                except (ValueError, TypeError, IndexError):
                    continue
            elif isinstance(v, dict):
                lat = v.get("lat")
                lon = v.get("lon")
                if lat is None or lon is None:
                    continue
                try:
                    lat, lon = float(lat), float(lon)
                except (ValueError, TypeError):
                    continue
                vessels.append(
                    {
                        "mmsi": str(v.get("mmsi", "")),
                        "name": (v.get("name") or "Unknown").strip(),
                        "type": _ship_type_label(v.get("type")),
                        "lat": round(lat, 5),
                        "lon": round(lon, 5),
                        "speed": v.get("speed"),
                        "heading": v.get("heading"),
                        "destination": v.get("destination"),
                        "flag": v.get("flag"),
                        "shipType": _ship_type_label(v.get("type")),
                        "source": "vesselfinder",
                    }
                )
        return vessels

    # ------------------------------------------------------------------
    # Source 3: MyShipTracking public JSON
    # ------------------------------------------------------------------
    async def _fetch_myshiptracking(self) -> list[dict]:
        url = "https://www.myshiptracking.com/requests/vesselsonmap.php"
        params = {"type": "json", "zoom": "2"}
        data = await self.fetch_json(
            url,
            params=params,
            cache_key=f"{self.cache_prefix}:myshiptracking",
        )
        vessels: list[dict] = []
        if not data:
            return vessels

        records = data if isinstance(data, list) else data.get("data", [])
        for v in records:
            if not isinstance(v, dict):
                continue
            lat = v.get("lat")
            lon = v.get("lng") or v.get("lon")
            if lat is None or lon is None:
                continue
            try:
                lat, lon = float(lat), float(lon)
            except (ValueError, TypeError):
                continue
            vessels.append(
                {
                    "mmsi": str(v.get("mmsi", "")),
                    "name": (v.get("name") or "Unknown").strip(),
                    "type": _ship_type_label(v.get("type")),
                    "lat": round(lat, 5),
                    "lon": round(lon, 5),
                    "speed": v.get("speed"),
                    "heading": v.get("heading"),
                    "destination": v.get("destination"),
                    "flag": v.get("flag") or v.get("country"),
                    "shipType": _ship_type_label(v.get("type")),
                    "source": "myshiptracking",
                }
            )
        return vessels

    # ------------------------------------------------------------------
    # Fallback: GDELT maritime keywords
    # ------------------------------------------------------------------
    async def _fetch_gdelt_fallback(self) -> list[dict]:
        """Return GDELT maritime news when all AIS APIs fail (no position data)."""
        articles = await self.fetch_gdelt(
            query="ship vessel cargo tanker maritime",
            max_records=15,
            category="maritime",
        )
        # Articles don't have positions; return empty vessel list but log
        logger.warning("VesselAgent: AIS APIs failed, GDELT fallback has no position data.")
        return []

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    async def fetch_data(self) -> dict:
        cache_key = f"{self.cache_prefix}:all"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        # Try all sources concurrently
        results = await asyncio.gather(
            self._fetch_datalastic(),
            self._fetch_vesselfinder(),
            self._fetch_myshiptracking(),
            return_exceptions=True,
        )

        vessels: list[dict] = []
        seen_mmsi: set[str] = set()

        for batch in results:
            if isinstance(batch, Exception):
                logger.warning("VesselAgent source error: %s", batch)
                continue
            for v in batch:
                mmsi = v.get("mmsi", "")
                key = mmsi or f"{v['lat']},{v['lon']}"
                if key in seen_mmsi:
                    continue
                seen_mmsi.add(key)
                vessels.append(v)

        if not vessels:
            await self._fetch_gdelt_fallback()

        result = {
            "vessels": vessels,
            "total": len(vessels),
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

        self._cache[cache_key] = result
        return result
