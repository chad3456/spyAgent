"""
Flight Agent — live aircraft positions from OpenSky Network (no auth required).

Returns the top 500 airborne aircraft with valid position data.
API docs: https://openskynetwork.github.io/opensky-api/rest.html
"""

import logging
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

OPENSKY_URL = "https://opensky-network.org/api/states/all"

# State vector field indices
IDX_ICAO24 = 0
IDX_CALLSIGN = 1
IDX_ORIGIN_COUNTRY = 2
IDX_TIME_POSITION = 3
IDX_LAST_CONTACT = 4
IDX_LONGITUDE = 5
IDX_LATITUDE = 6
IDX_BARO_ALTITUDE = 7
IDX_ON_GROUND = 8
IDX_VELOCITY = 9
IDX_TRUE_TRACK = 10
IDX_VERTICAL_RATE = 11
IDX_SENSORS = 12
IDX_GEO_ALTITUDE = 13
IDX_SQUAWK = 14
IDX_SPI = 15
IDX_POSITION_SOURCE = 16


class FlightAgent(BaseAgent):
    cache_prefix = "flights"

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
                if not isinstance(state, list) or len(state) < 17:
                    continue

                on_ground = state[IDX_ON_GROUND]
                lat = state[IDX_LATITUDE]
                lon = state[IDX_LONGITUDE]

                # Only airborne aircraft with valid position
                if on_ground or lat is None or lon is None:
                    continue

                icao24 = (state[IDX_ICAO24] or "").strip()
                callsign = (state[IDX_CALLSIGN] or "").strip()
                country = (state[IDX_ORIGIN_COUNTRY] or "").strip()
                altitude = state[IDX_BARO_ALTITUDE]
                velocity = state[IDX_VELOCITY]
                heading = state[IDX_TRUE_TRACK]
                vertical_rate = state[IDX_VERTICAL_RATE]
                squawk = state[IDX_SQUAWK]

                aircraft.append(
                    {
                        "icao24": icao24,
                        "callsign": callsign,
                        "country": country,
                        "lat": round(lat, 5),
                        "lon": round(lon, 5),
                        "altitude": round(altitude, 1) if altitude is not None else None,
                        "velocity": round(velocity, 1) if velocity is not None else None,
                        "heading": round(heading, 1) if heading is not None else None,
                        "vertical_rate": round(vertical_rate, 2) if vertical_rate is not None else None,
                        "squawk": squawk,
                    }
                )

                if len(aircraft) >= 500:
                    break

        result = {
            "aircraft": aircraft,
            "total": len(aircraft),
            "timestamp": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat() if timestamp else None,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

        self._cache[cache_key] = result
        return result
