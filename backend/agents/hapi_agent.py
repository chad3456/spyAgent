"""
HAPIAgent — fetches humanitarian conflict/protest data from OCHA's
Humanitarian API (HAPI): https://hapi.humdata.org/api/v1/

No API key required. Uses app_identifier query param.
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from .base_agent import BaseAgent
from .protest_agent import COUNTRY_CENTROIDS

logger = logging.getLogger(__name__)

HAPI_BASE = "https://hapi.humdata.org/api/v1/coordination-context/conflict-event"
APP_IDENTIFIER = "osint-protest-map"

# ISO3 → country name (reverse lookup for display)
_ISO3_TO_NAME: dict[str, str] = {
    "USA": "United States",
    "CAN": "Canada",
    "MEX": "Mexico",
    "GTM": "Guatemala",
    "HND": "Honduras",
    "SLV": "El Salvador",
    "NIC": "Nicaragua",
    "CRI": "Costa Rica",
    "PAN": "Panama",
    "CUB": "Cuba",
    "HTI": "Haiti",
    "DOM": "Dominican Republic",
    "JAM": "Jamaica",
    "BRA": "Brazil",
    "ARG": "Argentina",
    "COL": "Colombia",
    "CHL": "Chile",
    "PER": "Peru",
    "VEN": "Venezuela",
    "ECU": "Ecuador",
    "BOL": "Bolivia",
    "PRY": "Paraguay",
    "URY": "Uruguay",
    "GUY": "Guyana",
    "SUR": "Suriname",
    "GBR": "United Kingdom",
    "FRA": "France",
    "DEU": "Germany",
    "ITA": "Italy",
    "ESP": "Spain",
    "PRT": "Portugal",
    "NLD": "Netherlands",
    "BEL": "Belgium",
    "CHE": "Switzerland",
    "AUT": "Austria",
    "POL": "Poland",
    "CZE": "Czech Republic",
    "SVK": "Slovakia",
    "HUN": "Hungary",
    "ROU": "Romania",
    "BGR": "Bulgaria",
    "SRB": "Serbia",
    "HRV": "Croatia",
    "GRC": "Greece",
    "UKR": "Ukraine",
    "RUS": "Russia",
    "BLR": "Belarus",
    "SWE": "Sweden",
    "NOR": "Norway",
    "DNK": "Denmark",
    "FIN": "Finland",
    "IRL": "Ireland",
    "ISL": "Iceland",
    "TUR": "Turkey",
    "IRN": "Iran",
    "IRQ": "Iraq",
    "SYR": "Syria",
    "LBN": "Lebanon",
    "ISR": "Israel",
    "JOR": "Jordan",
    "SAU": "Saudi Arabia",
    "YEM": "Yemen",
    "OMN": "Oman",
    "ARE": "United Arab Emirates",
    "KWT": "Kuwait",
    "QAT": "Qatar",
    "BHR": "Bahrain",
    "EGY": "Egypt",
    "LBY": "Libya",
    "TUN": "Tunisia",
    "DZA": "Algeria",
    "MAR": "Morocco",
    "SDN": "Sudan",
    "ETH": "Ethiopia",
    "NGA": "Nigeria",
    "KEN": "Kenya",
    "ZAF": "South Africa",
    "GHA": "Ghana",
    "TZA": "Tanzania",
    "UGA": "Uganda",
    "COD": "Democratic Republic of the Congo",
    "CMR": "Cameroon",
    "CIV": "Ivory Coast",
    "MDG": "Madagascar",
    "MOZ": "Mozambique",
    "ZMB": "Zambia",
    "ZWE": "Zimbabwe",
    "AGO": "Angola",
    "SOM": "Somalia",
    "MLI": "Mali",
    "BFA": "Burkina Faso",
    "SEN": "Senegal",
    "GIN": "Guinea",
    "CHN": "China",
    "IND": "India",
    "JPN": "Japan",
    "KOR": "South Korea",
    "PRK": "North Korea",
    "IDN": "Indonesia",
    "PHL": "Philippines",
    "VNM": "Vietnam",
    "THA": "Thailand",
    "MYS": "Malaysia",
    "SGP": "Singapore",
    "MMR": "Myanmar",
    "KHM": "Cambodia",
    "LAO": "Laos",
    "BGD": "Bangladesh",
    "PAK": "Pakistan",
    "AFG": "Afghanistan",
    "NPL": "Nepal",
    "LKA": "Sri Lanka",
    "KAZ": "Kazakhstan",
    "UZB": "Uzbekistan",
    "TWN": "Taiwan",
    "HKG": "Hong Kong",
    "AUS": "Australia",
    "NZL": "New Zealand",
    "PNG": "Papua New Guinea",
}


def _hapi_threat(fatalities: int, event_count: int) -> str:
    """Determine threat level from fatalities and event count."""
    if fatalities > 5:
        return "CRITICAL"
    if fatalities > 0:
        return "HIGH"
    if event_count > 10:
        return "MEDIUM"
    return "LOW"


def _make_hapi_id(resource_hdx_id: str, location_code: str, date: str, event_type: str) -> str:
    """Generate a stable event ID."""
    if resource_hdx_id:
        return resource_hdx_id
    raw = f"{location_code}:{date}:{event_type}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]


class HAPIAgent(BaseAgent):
    """Fetches humanitarian protest/conflict data from OCHA HAPI."""

    cache_prefix = "hapi"

    async def fetch_data(self) -> dict:
        protests_task = self._fetch_hapi_events("Protests")
        demonstrations_task = self._fetch_hapi_events("Demonstrations")

        results = await asyncio.gather(
            protests_task, demonstrations_task, return_exceptions=True
        )

        all_events: list[dict] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("HAPI fetch error: %s", result)
            elif isinstance(result, list):
                all_events.extend(result)

        # Deduplicate by id
        seen: set[str] = set()
        deduped: list[dict] = []
        for ev in all_events:
            eid = ev.get("id", "")
            if eid and eid not in seen:
                seen.add(eid)
                deduped.append(ev)

        if not deduped:
            logger.warning("No HAPI data returned — serving demo seed data")
            try:
                import sys, os
                sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
                from demo_data import get_demo_hapi
                return get_demo_hapi()
            except Exception as e:
                logger.error("Failed to load HAPI demo data: %s", e)

        return {
            "conflictEvents": deduped,
            "totalCount": len(deduped),
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
        }

    async def _fetch_hapi_events(self, event_type: str) -> list[dict]:
        """Fetch a single event_type page from HAPI conflict-event endpoint."""
        params = {
            "output_format": "json",
            "limit": "1000",
            "offset": "0",
            "event_type": event_type,
            "app_identifier": APP_IDENTIFIER,
        }
        cache_key = f"{self.cache_prefix}:hapi:{event_type}"
        data = await self.fetch_json(HAPI_BASE, params=params, cache_key=cache_key)
        if not data:
            return []

        records = data.get("data") or []
        events: list[dict] = []

        for rec in records:
            location_code = rec.get("location_code", "") or ""
            location_name = rec.get("location_name", "") or ""
            admin1 = rec.get("admin1_name", "") or ""
            resource_hdx_id = rec.get("resource_hdx_id", "") or ""
            date_str = rec.get("date", "") or ""
            rec_event_type = rec.get("event_type", event_type) or event_type

            try:
                event_count = int(rec.get("events", 0) or 0)
            except (ValueError, TypeError):
                event_count = 0

            try:
                fatalities = int(rec.get("fatalities", 0) or 0)
            except (ValueError, TypeError):
                fatalities = 0

            # Geocode via ISO3 centroid
            iso3 = location_code.upper() if location_code else ""
            lat: Optional[float] = None
            lon: Optional[float] = None
            if iso3 in COUNTRY_CENTROIDS:
                lat, lon = COUNTRY_CENTROIDS[iso3]

            if lat is None or lon is None:
                continue

            country_display = _ISO3_TO_NAME.get(iso3, location_name or iso3)

            # Format date — HAPI typically returns YYYY-MM-DD
            date_out = date_str[:10] if date_str else ""

            event_id = _make_hapi_id(resource_hdx_id, location_code, date_out, rec_event_type)
            threat = _hapi_threat(fatalities, event_count)

            events.append({
                "id": event_id,
                "country": country_display,
                "countryCode": iso3,
                "admin1": admin1,
                "eventType": rec_event_type,
                "eventCount": event_count,
                "fatalities": fatalities,
                "date": date_out,
                "lat": lat,
                "lon": lon,
                "threatLevel": threat,
                "dataSource": "HAPI/OCHA",
            })

        return events
