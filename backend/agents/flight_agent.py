"""
Flight Agent — live aircraft positions with a 3-source fallback chain.

Source priority (all free, no auth):
1. OpenSky Network REST API  https://opensky-network.org/api/states/all
2. ADSB.lol (community ADS-B) https://api.adsb.lol/v2/aircraft
3. airplanes.live              https://api.airplanes.live/v2/aircraft

Returns up to 500 airborne aircraft with valid lat/lon.
Cache TTL: 30 seconds (matches live data refresh rate).
"""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from .base_agent import BaseAgent, _HEADERS

logger = logging.getLogger(__name__)

# ── API endpoints ──────────────────────────────────────────────────────────────
OPENSKY_URL       = "https://opensky-network.org/api/states/all"
ADSBLOL_URL       = "https://api.adsb.lol/v2/aircraft"
AIRPLANESLIVE_URL = "https://api.airplanes.live/v2/aircraft"

# OpenSky state-vector field indices
IDX_ICAO24        = 0
IDX_CALLSIGN      = 1
IDX_ORIGIN_COUNTRY= 2
IDX_LONGITUDE     = 5
IDX_LATITUDE      = 6
IDX_BARO_ALTITUDE = 7
IDX_ON_GROUND     = 8
IDX_VELOCITY      = 9
IDX_TRUE_TRACK    = 10
IDX_VERTICAL_RATE = 11
IDX_GEO_ALTITUDE  = 13
IDX_SQUAWK        = 14

MAX_AIRCRAFT = 500


def _make_record(icao24, callsign, country, lat, lon, altitude, velocity, heading, vrate, squawk):
    return {
        "icao24":        (icao24 or "").strip(),
        "callsign":      (callsign or "").strip(),
        "country":       (country or "").strip(),
        "lat":           round(float(lat), 5),
        "lon":           round(float(lon), 5),
        "altitude":      round(float(altitude), 1) if altitude is not None else None,
        "velocity":      round(float(velocity), 1) if velocity is not None else None,
        "heading":       round(float(heading), 1)  if heading   is not None else None,
        "vertical_rate": round(float(vrate), 2)    if vrate     is not None else None,
        "squawk":        squawk or None,
    }


# ── Source 1: OpenSky Network ─────────────────────────────────────────────────

async def _fetch_opensky(timeout: float) -> list[dict]:
    """Fetch from OpenSky REST API (anonymous, rate-limited to 100 req/10 min)."""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=_HEADERS) as client:
            resp = await client.get(OPENSKY_URL)
            if resp.status_code == 429:
                logger.warning("OpenSky rate-limited (429)")
                return []
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.info("OpenSky unavailable: %s", exc)
        return []

    states = data.get("states") or []
    aircraft: list[dict] = []

    for state in states:
        if not isinstance(state, list) or len(state) < 15:
            continue
        on_ground = state[IDX_ON_GROUND]
        lat = state[IDX_LATITUDE]
        lon = state[IDX_LONGITUDE]
        if on_ground or lat is None or lon is None:
            continue
        alt = state[IDX_BARO_ALTITUDE] or state[IDX_GEO_ALTITUDE]
        aircraft.append(_make_record(
            state[IDX_ICAO24], state[IDX_CALLSIGN], state[IDX_ORIGIN_COUNTRY],
            lat, lon, alt, state[IDX_VELOCITY], state[IDX_TRUE_TRACK],
            state[IDX_VERTICAL_RATE], state[IDX_SQUAWK],
        ))
        if len(aircraft) >= MAX_AIRCRAFT:
            break

    logger.info("OpenSky: %d aircraft", len(aircraft))
    return aircraft


# ── Source 2: ADSB.lol ───────────────────────────────────────────────────────

async def _fetch_adsblol(timeout: float) -> list[dict]:
    """Fetch from adsb.lol community feed. Returns all aircraft globally."""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=_HEADERS) as client:
            resp = await client.get(ADSBLOL_URL)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.info("adsb.lol unavailable: %s", exc)
        return []

    # adsb.lol returns {"ac": [...]} where each ac is a dict
    raw_list = data.get("ac") or data.get("aircraft") or []
    aircraft: list[dict] = []

    for ac in raw_list:
        if not isinstance(ac, dict):
            continue
        lat = ac.get("lat")
        lon = ac.get("lon")
        if lat is None or lon is None:
            continue
        # Skip ground vehicles
        if ac.get("gnd") or ac.get("ground"):
            continue
        aircraft.append(_make_record(
            ac.get("hex") or ac.get("icao24", ""),
            ac.get("flight") or ac.get("callsign", ""),
            ac.get("ownOp") or ac.get("country", ""),
            lat, lon,
            ac.get("alt_baro") or ac.get("altitude"),
            ac.get("gs") or ac.get("velocity"),       # ground speed
            ac.get("track") or ac.get("heading"),
            ac.get("baro_rate") or ac.get("vertical_rate"),
            ac.get("squawk"),
        ))
        if len(aircraft) >= MAX_AIRCRAFT:
            break

    logger.info("adsb.lol: %d aircraft", len(aircraft))
    return aircraft


# ── Source 3: airplanes.live ─────────────────────────────────────────────────

async def _fetch_airplaneslive(timeout: float) -> list[dict]:
    """Fetch from airplanes.live community ADS-B aggregator."""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=_HEADERS) as client:
            resp = await client.get(AIRPLANESLIVE_URL)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.info("airplanes.live unavailable: %s", exc)
        return []

    raw_list = data.get("ac") or data.get("aircraft") or []
    aircraft: list[dict] = []

    for ac in raw_list:
        if not isinstance(ac, dict):
            continue
        lat = ac.get("lat")
        lon = ac.get("lon")
        if lat is None or lon is None:
            continue
        if ac.get("gnd") or ac.get("ground"):
            continue
        aircraft.append(_make_record(
            ac.get("hex") or ac.get("icao24", ""),
            ac.get("flight") or ac.get("callsign", ""),
            ac.get("ownOp") or ac.get("country", ""),
            lat, lon,
            ac.get("alt_baro") or ac.get("altitude"),
            ac.get("gs") or ac.get("velocity"),
            ac.get("track") or ac.get("heading"),
            ac.get("baro_rate") or ac.get("vertical_rate"),
            ac.get("squawk"),
        ))
        if len(aircraft) >= MAX_AIRCRAFT:
            break

    logger.info("airplanes.live: %d aircraft", len(aircraft))
    return aircraft


# ── Agent ─────────────────────────────────────────────────────────────────────

class FlightAgent(BaseAgent):
    cache_prefix = "flights"

    async def fetch_data(self) -> dict:
        cache_key = f"{self.cache_prefix}:all"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        # Try all three sources concurrently; use first that returns data
        opensky_task, adsblol_task, aplive_task = await asyncio.gather(
            _fetch_opensky(self.timeout),
            _fetch_adsblol(self.timeout),
            _fetch_airplaneslive(self.timeout),
            return_exceptions=True,
        )

        # Pick the first successful non-empty result
        source = "none"
        aircraft: list[dict] = []

        for result, label in [
            (opensky_task, "opensky"),
            (adsblol_task, "adsb.lol"),
            (aplive_task, "airplanes.live"),
        ]:
            if isinstance(result, Exception):
                logger.warning("%s raised exception: %s", label, result)
                continue
            if result:                     # non-empty list
                aircraft = result[:MAX_AIRCRAFT]
                source = label
                logger.info("FlightAgent using source=%s count=%d", source, len(aircraft))
                break

        if not aircraft:
            logger.warning("FlightAgent: all sources returned no data")

        result_dict = {
            "aircraft":  aircraft,
            "total":     len(aircraft),
            "source":    source,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

        # Only cache non-empty results to allow immediate retry on next request
        if aircraft:
            self._cache[cache_key] = result_dict

        return result_dict
