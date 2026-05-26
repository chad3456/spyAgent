"""
Military Flight Agent — filters OpenSky Network data for known military aircraft.

Detection strategy (layered):
1. ICAO hex prefix ranges for US (AE****), UK (43C***), France (3C****, partial) etc.
2. Callsign prefixes that indicate military operations.
3. Squawk codes commonly assigned to military flights.

API: https://openskynetwork.github.io/opensky-api/rest.html  (no auth needed)
"""
from __future__ import annotations


import logging
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

OPENSKY_URL = "https://opensky-network.org/api/states/all"

# ---------------------------------------------------------------------------
# Military ICAO hex ranges  (lower, upper, nation)
# ---------------------------------------------------------------------------
MILITARY_ICAO_RANGES = [
    (0xAE0000, 0xAEFFFF, "US"),        # US military
    (0x43C000, 0x43CFFF, "UK"),        # UK military
    (0x7C0000, 0x7FFFFF, "Australia"), # Aus (partial mil)
    (0x898000, 0x898FFF, "India"),     # India military
    (0x720000, 0x727FFF, "Iran"),      # Iran (partial)
    (0x140000, 0x147FFF, "Russia"),    # Russia military band
    (0x3A0000, 0x3AFFFF, "France"),    # France military
    (0x68C000, 0x68CFFF, "Brazil"),    # Brazil FAB
    (0x0A0000, 0x0AFFFF, "China"),     # China PLA AF band
]

# ---------------------------------------------------------------------------
# Callsign prefixes → military unit / nation
# ---------------------------------------------------------------------------
MILITARY_CALLSIGN_PREFIXES: dict[str, str] = {
    "USAF": "US Air Force",
    "NAVY": "US Navy",
    "ARMY": "US Army",
    "USMC": "US Marines",
    "ANG": "Air National Guard",
    "AFSOC": "US Air Force SOC",
    "REACH": "USAF AMC",
    "ATLAS": "USAF AMC",
    "ROCKY": "USAF",
    "VIPER": "USAF",
    "GHOST": "USAF",
    "RAIDER": "USAF B-2",
    "SPAR": "USAF VIP",
    "RCH": "USAF AMC Reach",
    "CNV": "US Navy Conv",
    "PAT": "USAF Patriot",
    "FORTE": "USAF TACAMO",
    "LEAR": "USAF Learjet",
    "GATOR": "USAF",
    "RAF": "Royal Air Force",
    "RRR": "UK Royal Air Force",
    "ASCOT": "RAF Air Transport",
    "TARTAN": "RAF",
    "NATO": "NATO",
    "OTAN": "NATO",
    "GERMAN": "Luftwaffe",
    "GAF": "German Air Force",
    "LFT": "Luftwaffe",
    "IAF": "Israeli Air Force",
    "ISAF": "ISAF",
    "FRENCHAF": "French Air Force",
    "COTAM": "French AF Transport",
    "FAF": "French Air Force",
    "THFR": "French Navy",
    "CYGNE": "French AF",
    "MRTT": "Multi-role tanker",
    "MMF": "NATO Tanker",
    "SAAF": "South African AF",
    "RSAF": "Royal Saudi AF",
    "TURK": "Turkish Air Force",
    "THY": "Turkish AF",
    "PAF": "Pakistan Air Force",
    "ILYICH": "Russia",
    "RSD": "Russia",
    "RFF": "Russia",
}

# Squawk codes commonly associated with military
MILITARY_SQUAWKS = {"7777", "7400", "7401", "7500", "7600", "7700"}

# State vector field indices
IDX_ICAO24 = 0
IDX_CALLSIGN = 1
IDX_ORIGIN_COUNTRY = 2
IDX_LONGITUDE = 5
IDX_LATITUDE = 6
IDX_BARO_ALTITUDE = 7
IDX_ON_GROUND = 8
IDX_VELOCITY = 9
IDX_TRUE_TRACK = 10
IDX_VERTICAL_RATE = 11
IDX_SQUAWK = 14


def _is_military_icao(hex_str: str) -> tuple[bool, str]:
    """Return (True, nation) if the ICAO24 hex falls in a known military range."""
    try:
        value = int(hex_str, 16)
    except (ValueError, TypeError):
        return False, ""
    for lo, hi, nation in MILITARY_ICAO_RANGES:
        if lo <= value <= hi:
            return True, nation
    return False, ""


def _military_callsign_match(callsign: str) -> tuple[bool, str]:
    """Return (True, unit description) if callsign starts with a known military prefix."""
    upper = callsign.upper().strip()
    for prefix, unit in MILITARY_CALLSIGN_PREFIXES.items():
        if upper.startswith(prefix):
            return True, unit
    return False, ""


class MilitaryFlightAgent(BaseAgent):
    cache_prefix = "military_flights"

    async def fetch_data(self) -> dict:
        cache_key = f"{self.cache_prefix}:all"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        data = await self.fetch_json(OPENSKY_URL, cache_key=f"{self.cache_prefix}:raw")

        aircraft: list[dict] = []

        if data and isinstance(data, dict):
            states = data.get("states") or []
            timestamp = data.get("time", 0)

            for state in states:
                if not isinstance(state, list) or len(state) < 15:
                    continue

                lat = state[IDX_LATITUDE]
                lon = state[IDX_LONGITUDE]
                if lat is None or lon is None:
                    continue

                icao24 = (state[IDX_ICAO24] or "").strip()
                callsign = (state[IDX_CALLSIGN] or "").strip()
                on_ground = state[IDX_ON_GROUND]
                squawk = (state[IDX_SQUAWK] or "").strip()
                country = (state[IDX_ORIGIN_COUNTRY] or "").strip()

                military = False
                nation = country
                unit_label = ""

                # Check ICAO hex range
                icao_mil, icao_nation = _is_military_icao(icao24)
                if icao_mil:
                    military = True
                    nation = icao_nation
                    unit_label = f"{icao_nation} Military"

                # Check callsign prefix
                if not military and callsign:
                    cs_mil, cs_unit = _military_callsign_match(callsign)
                    if cs_mil:
                        military = True
                        unit_label = cs_unit

                # Check squawk
                if not military and squawk in MILITARY_SQUAWKS:
                    military = True
                    unit_label = f"Squawk {squawk}"

                if not military:
                    continue

                altitude = state[IDX_BARO_ALTITUDE]
                velocity = state[IDX_VELOCITY]
                heading = state[IDX_TRUE_TRACK]
                vertical_rate = state[IDX_VERTICAL_RATE]

                aircraft.append(
                    {
                        "icao24": icao24,
                        "callsign": callsign,
                        "country": country,
                        "nation": nation,
                        "unit": unit_label,
                        "lat": round(lat, 5),
                        "lon": round(lon, 5),
                        "altitude": round(altitude, 1) if altitude is not None else None,
                        "velocity": round(velocity, 1) if velocity is not None else None,
                        "heading": round(heading, 1) if heading is not None else None,
                        "vertical_rate": round(vertical_rate, 2) if vertical_rate is not None else None,
                        "squawk": squawk,
                        "on_ground": bool(on_ground),
                        "military": True,
                    }
                )

        result = {
            "aircraft": aircraft,
            "total": len(aircraft),
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

        self._cache[cache_key] = result
        return result
