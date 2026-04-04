"""
ProtestAgent — fetches global protest/demonstration data from:
  - GDELT Document API V2 (free, no key required)
  - ACLED API (optional, requires ACLED_API_KEY + ACLED_EMAIL env vars)
"""

import asyncio
import hashlib
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Country centroids: ISO3 / country name → (lat, lon)
# ---------------------------------------------------------------------------
COUNTRY_CENTROIDS: dict[str, tuple[float, float]] = {
    # North America
    "USA": (37.09, -95.71),
    "CAN": (56.13, -106.35),
    "MEX": (23.63, -102.55),
    "GTM": (15.78, -90.23),
    "HND": (15.20, -86.24),
    "SLV": (13.79, -88.90),
    "NIC": (12.87, -85.21),
    "CRI": (9.75, -83.75),
    "PAN": (8.54, -80.78),
    "CUB": (21.52, -77.78),
    "HTI": (18.97, -72.29),
    "DOM": (18.74, -70.16),
    "JAM": (18.11, -77.30),
    # South America
    "BRA": (-14.24, -51.93),
    "ARG": (-38.42, -63.62),
    "COL": (4.57, -74.30),
    "CHL": (-35.68, -71.54),
    "PER": (-9.19, -75.02),
    "VEN": (6.42, -66.59),
    "ECU": (-1.83, -78.18),
    "BOL": (-16.29, -63.59),
    "PRY": (-23.44, -58.44),
    "URY": (-32.52, -55.77),
    "GUY": (4.86, -58.93),
    "SUR": (3.92, -56.03),
    # Europe
    "GBR": (55.38, -3.44),
    "FRA": (46.23, 2.21),
    "DEU": (51.17, 10.45),
    "ITA": (41.87, 12.57),
    "ESP": (40.46, -3.75),
    "PRT": (39.40, -8.22),
    "NLD": (52.13, 5.29),
    "BEL": (50.50, 4.47),
    "CHE": (46.82, 8.23),
    "AUT": (47.52, 14.55),
    "POL": (51.92, 19.15),
    "CZE": (49.82, 15.47),
    "SVK": (48.67, 19.70),
    "HUN": (47.16, 19.50),
    "ROU": (45.94, 24.97),
    "BGR": (42.73, 25.49),
    "SRB": (44.02, 21.01),
    "HRV": (45.10, 15.20),
    "GRC": (39.07, 21.82),
    "UKR": (48.38, 31.17),
    "RUS": (61.52, 105.32),
    "BLR": (53.71, 27.95),
    "SWE": (60.13, 18.64),
    "NOR": (60.47, 8.47),
    "DNK": (56.26, 9.50),
    "FIN": (61.92, 25.75),
    "IRL": (53.41, -8.24),
    "ISL": (64.96, -19.02),
    # Middle East & North Africa
    "TUR": (38.96, 35.24),
    "IRN": (32.43, 53.69),
    "IRQ": (33.22, 43.68),
    "SYR": (34.80, 38.99),
    "LBN": (33.85, 35.86),
    "ISR": (31.05, 34.85),
    "JOR": (30.59, 36.24),
    "SAU": (23.89, 45.08),
    "YEM": (15.55, 48.52),
    "OMN": (21.51, 55.92),
    "ARE": (23.42, 53.85),
    "KWT": (29.31, 47.48),
    "QAT": (25.35, 51.18),
    "BHR": (26.00, 50.55),
    "EGY": (26.82, 30.80),
    "LBY": (26.34, 17.23),
    "TUN": (33.89, 9.54),
    "DZA": (28.03, 1.66),
    "MAR": (31.79, -7.09),
    "SDN": (12.86, 30.22),
    # Sub-Saharan Africa
    "ETH": (9.15, 40.49),
    "NGA": (9.08, 8.68),
    "KEN": (-0.02, 37.91),
    "ZAF": (-28.47, 24.68),
    "GHA": (7.95, -1.02),
    "TZA": (-6.37, 34.89),
    "UGA": (1.37, 32.29),
    "COD": (-4.04, 21.76),
    "CMR": (3.85, 11.50),
    "CIV": (7.54, -5.55),
    "MDG": (-18.77, 46.87),
    "MOZ": (-18.67, 35.53),
    "ZMB": (-13.13, 27.85),
    "ZWE": (-19.02, 29.15),
    "AGO": (-11.20, 17.87),
    "SOM": (5.15, 46.20),
    "MLI": (17.57, -3.99),
    "BFA": (12.36, -1.56),
    "SEN": (14.50, -14.45),
    "GIN": (11.00, -10.94),
    # Asia
    "CHN": (35.86, 104.20),
    "IND": (20.59, 78.96),
    "JPN": (36.20, 138.25),
    "KOR": (35.91, 127.77),
    "PRK": (40.34, 127.51),
    "IDN": (-0.79, 113.92),
    "PHL": (12.88, 121.77),
    "VNM": (14.06, 108.28),
    "THA": (15.87, 100.99),
    "MYS": (4.21, 108.96),
    "SGP": (1.35, 103.82),
    "MMR": (17.11, 96.96),
    "KHM": (12.57, 104.99),
    "LAO": (19.86, 102.50),
    "BGD": (23.68, 90.36),
    "PAK": (30.38, 69.35),
    "AFG": (33.94, 67.71),
    "NPL": (28.39, 84.12),
    "LKA": (7.87, 80.77),
    "KAZ": (47.17, 67.00),
    "UZB": (41.38, 64.59),
    "TWN": (23.70, 121.00),
    "HKG": (22.31, 114.17),
    # Oceania
    "AUS": (-25.27, 133.78),
    "NZL": (-40.90, 174.89),
    "PNG": (-6.31, 143.96),
}

# ---------------------------------------------------------------------------
# Country name → centroid (for title scanning)
# ---------------------------------------------------------------------------
COUNTRY_NAME_MAP: dict[str, tuple[float, float]] = {
    "united states": (37.09, -95.71),
    "us": (37.09, -95.71),
    "usa": (37.09, -95.71),
    "america": (37.09, -95.71),
    "canada": (56.13, -106.35),
    "mexico": (23.63, -102.55),
    "brazil": (-14.24, -51.93),
    "argentina": (-38.42, -63.62),
    "colombia": (4.57, -74.30),
    "chile": (-35.68, -71.54),
    "peru": (-9.19, -75.02),
    "venezuela": (6.42, -66.59),
    "ecuador": (-1.83, -78.18),
    "bolivia": (-16.29, -63.59),
    "paraguay": (-23.44, -58.44),
    "uruguay": (-32.52, -55.77),
    "united kingdom": (55.38, -3.44),
    "uk": (55.38, -3.44),
    "britain": (55.38, -3.44),
    "england": (52.36, -1.17),
    "france": (46.23, 2.21),
    "germany": (51.17, 10.45),
    "italy": (41.87, 12.57),
    "spain": (40.46, -3.75),
    "portugal": (39.40, -8.22),
    "netherlands": (52.13, 5.29),
    "belgium": (50.50, 4.47),
    "switzerland": (46.82, 8.23),
    "austria": (47.52, 14.55),
    "poland": (51.92, 19.15),
    "czech republic": (49.82, 15.47),
    "czechia": (49.82, 15.47),
    "slovakia": (48.67, 19.70),
    "hungary": (47.16, 19.50),
    "romania": (45.94, 24.97),
    "bulgaria": (42.73, 25.49),
    "serbia": (44.02, 21.01),
    "croatia": (45.10, 15.20),
    "greece": (39.07, 21.82),
    "ukraine": (48.38, 31.17),
    "russia": (61.52, 105.32),
    "belarus": (53.71, 27.95),
    "sweden": (60.13, 18.64),
    "norway": (60.47, 8.47),
    "denmark": (56.26, 9.50),
    "finland": (61.92, 25.75),
    "ireland": (53.41, -8.24),
    "turkey": (38.96, 35.24),
    "iran": (32.43, 53.69),
    "iraq": (33.22, 43.68),
    "syria": (34.80, 38.99),
    "lebanon": (33.85, 35.86),
    "israel": (31.05, 34.85),
    "jordan": (30.59, 36.24),
    "saudi arabia": (23.89, 45.08),
    "yemen": (15.55, 48.52),
    "egypt": (26.82, 30.80),
    "libya": (26.34, 17.23),
    "tunisia": (33.89, 9.54),
    "algeria": (28.03, 1.66),
    "morocco": (31.79, -7.09),
    "sudan": (12.86, 30.22),
    "ethiopia": (9.15, 40.49),
    "nigeria": (9.08, 8.68),
    "kenya": (-0.02, 37.91),
    "south africa": (-28.47, 24.68),
    "ghana": (7.95, -1.02),
    "tanzania": (-6.37, 34.89),
    "uganda": (1.37, 32.29),
    "china": (35.86, 104.20),
    "india": (20.59, 78.96),
    "japan": (36.20, 138.25),
    "south korea": (35.91, 127.77),
    "korea": (35.91, 127.77),
    "indonesia": (-0.79, 113.92),
    "philippines": (12.88, 121.77),
    "vietnam": (14.06, 108.28),
    "thailand": (15.87, 100.99),
    "malaysia": (4.21, 108.96),
    "singapore": (1.35, 103.82),
    "myanmar": (17.11, 96.96),
    "burma": (17.11, 96.96),
    "cambodia": (12.57, 104.99),
    "bangladesh": (23.68, 90.36),
    "pakistan": (30.38, 69.35),
    "afghanistan": (33.94, 67.71),
    "nepal": (28.39, 84.12),
    "sri lanka": (7.87, 80.77),
    "kazakhstan": (47.17, 67.00),
    "uzbekistan": (41.38, 64.59),
    "taiwan": (23.70, 121.00),
    "hong kong": (22.31, 114.17),
    "australia": (-25.27, 133.78),
    "new zealand": (-40.90, 174.89),
    "guatemala": (15.78, -90.23),
    "honduras": (15.20, -86.24),
    "el salvador": (13.79, -88.90),
    "nicaragua": (12.87, -85.21),
    "costa rica": (9.75, -83.75),
    "panama": (8.54, -80.78),
    "cuba": (21.52, -77.78),
    "haiti": (18.97, -72.29),
    "dominican republic": (18.74, -70.16),
    "jamaica": (18.11, -77.30),
    "mali": (17.57, -3.99),
    "burkina faso": (12.36, -1.56),
    "senegal": (14.50, -14.45),
    "guinea": (11.00, -10.94),
    "somalia": (5.15, 46.20),
    "angola": (-11.20, 17.87),
    "zimbabwe": (-19.02, 29.15),
    "zambia": (-13.13, 27.85),
    "mozambique": (-18.67, 35.53),
    "madagascar": (-18.77, 46.87),
    "democratic republic of the congo": (-4.04, 21.76),
    "drc": (-4.04, 21.76),
    "congo": (-4.04, 21.76),
    "cameroon": (3.85, 11.50),
    "ivory coast": (7.54, -5.55),
    "cote d'ivoire": (7.54, -5.55),
}

# ---------------------------------------------------------------------------
# Threat level keyword mapping
# ---------------------------------------------------------------------------
THREAT_KEYWORDS: dict[str, list[str]] = {
    "CRITICAL": [
        "riot", "violent", "killed", "deaths", "fatalities",
        "army", "troops", "crackdown", "gunfire", "live ammunition",
    ],
    "HIGH": [
        "clash", "arrested", "tear gas", "water cannon", "rubber bullets",
        "injured", "wounded", "standoff",
    ],
    "MEDIUM": [
        "protest", "demonstration", "march", "blockade", "strike",
        "walkout", "shutdown",
    ],
    "LOW": [
        "rally", "vigil", "gathering", "assembly", "petition", "picket",
    ],
}

_THREAT_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

GDELT_DOC_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
ACLED_BASE = "https://api.acleddata.com/acled/read"


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _extract_location_from_title(title: str) -> Optional[tuple[float, float]]:
    """Scan title text for any known country name and return its centroid."""
    if not title:
        return None
    lower = title.lower()
    # Check longer names first to avoid partial matches (e.g. "south korea" before "korea")
    for name in sorted(COUNTRY_NAME_MAP.keys(), key=len, reverse=True):
        if re.search(r"\b" + re.escape(name) + r"\b", lower):
            return COUNTRY_NAME_MAP[name]
    return None


def _assess_threat(title: str, event_type: str = "") -> str:
    """Return highest threat level matching keywords in title + event_type."""
    combined = (title + " " + event_type).lower()
    for level in _THREAT_ORDER:
        for kw in THREAT_KEYWORDS[level]:
            if kw in combined:
                return level
    return "LOW"


def _parse_gdelt_date(date_str: str) -> str:
    """Convert GDELT date format '20240401T120000Z' to ISO 8601."""
    if not date_str:
        return ""
    try:
        # e.g. "20240401T120000Z" or "20240401120000"
        clean = date_str.replace("T", "").replace("Z", "").replace("-", "")
        if len(clean) >= 14:
            dt = datetime.strptime(clean[:14], "%Y%m%d%H%M%S")
        elif len(clean) >= 8:
            dt = datetime.strptime(clean[:8], "%Y%m%d")
        else:
            return date_str
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except (ValueError, TypeError):
        return date_str


def _make_event_id(url: str) -> str:
    """Return first 12 hex chars of md5(url)."""
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------------------
# ProtestAgent
# ---------------------------------------------------------------------------

class ProtestAgent(BaseAgent):
    """Fetches global protest events from GDELT and optionally ACLED."""

    cache_prefix = "protest"

    async def fetch_data(self) -> dict:
        acled_key = os.environ.get("ACLED_API_KEY", "")
        acled_email = os.environ.get("ACLED_EMAIL", "")

        tasks = [self._fetch_gdelt_protests()]
        if acled_key and acled_email:
            tasks.append(self._fetch_acled_protests())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_events: list[dict] = []
        sources: list[str] = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                source_name = "GDELT" if i == 0 else "ACLED"
                logger.error("%s fetch failed: %s", source_name, result)
            elif isinstance(result, list):
                all_events.extend(result)
                if result:
                    sources.append(result[0].get("dataSource", "UNKNOWN"))

        # Deduplicate by id
        seen: set[str] = set()
        deduped: list[dict] = []
        for ev in all_events:
            eid = ev.get("id", "")
            if eid and eid not in seen:
                seen.add(eid)
                deduped.append(ev)

        # Threat summary
        threat_summary: dict[str, int] = {lvl: 0 for lvl in _THREAT_ORDER}
        for ev in deduped:
            lvl = ev.get("threatLevel", "LOW")
            threat_summary[lvl] = threat_summary.get(lvl, 0) + 1

        unique_sources = list(dict.fromkeys(sources))  # preserve order, deduplicate

        # If no live data was returned (network blocked / APIs down), use demo data
        if not deduped:
            logger.warning("No live protest data fetched — serving demo seed data")
            try:
                import sys, os
                sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
                from demo_data import get_demo_protests
                return get_demo_protests()
            except Exception as e:
                logger.error("Failed to load demo data: %s", e)

        return {
            "events": deduped,
            "totalCount": len(deduped),
            "sources": unique_sources,
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
            "threatSummary": threat_summary,
        }

    async def _fetch_gdelt_protests(self) -> list[dict]:
        """Fetch protest articles from GDELT Doc API V2."""
        params = {
            "query": "protest OR demonstration OR rally OR riot OR strike",
            "mode": "artlist",
            "format": "json",
            "maxrecords": "250",
            "sourcelang": "english",
            "timespan": "24h",
        }
        cache_key = f"{self.cache_prefix}:gdelt_protests"
        data = await self.fetch_json(GDELT_DOC_BASE, params=params, cache_key=cache_key)
        if not data:
            return []

        articles = data.get("articles") or []
        events: list[dict] = []

        for art in articles:
            url = art.get("url", "")
            title = art.get("title", "")
            if not url or not title:
                continue

            sourcecountry = art.get("sourcecountry", "") or ""
            domain = art.get("domain", "") or ""
            seendate = art.get("seendate", "")
            socialimage = art.get("socialimage") or None
            language = art.get("language", "")

            # Geocode: title first, then sourcecountry centroid
            lat, lon, resolved_country = None, None, sourcecountry

            loc = _extract_location_from_title(title)
            if loc:
                lat, lon = loc
            else:
                # Try sourcecountry field in COUNTRY_NAME_MAP
                sc_lower = sourcecountry.lower()
                if sc_lower in COUNTRY_NAME_MAP:
                    lat, lon = COUNTRY_NAME_MAP[sc_lower]
                else:
                    # Try ISO3 via COUNTRY_CENTROIDS (GDELT uses country codes sometimes)
                    sc_upper = sourcecountry.upper()
                    if sc_upper in COUNTRY_CENTROIDS:
                        lat, lon = COUNTRY_CENTROIDS[sc_upper]

            # Skip if no location resolved
            if lat is None or lon is None:
                continue

            threat = _assess_threat(title)

            events.append({
                "id": _make_event_id(url),
                "title": title,
                "url": url,
                "source": domain,
                "sourcecountry": sourcecountry,
                "publishedAt": _parse_gdelt_date(seendate),
                "image": socialimage,
                "lat": lat,
                "lon": lon,
                "country": resolved_country,
                "threatLevel": threat,
                "eventType": "Protest",
                "dataSource": "GDELT",
                "language": language,
            })

        return events

    async def _fetch_acled_protests(self) -> list[dict]:
        """Fetch protest events from ACLED API (requires env vars)."""
        acled_key = os.environ.get("ACLED_API_KEY", "")
        acled_email = os.environ.get("ACLED_EMAIL", "")
        if not acled_key or not acled_email:
            return []

        params = {
            "key": acled_key,
            "email": acled_email,
            "event_type": "Protests",
            "limit": "500",
            "fields": (
                "event_date|country|admin1|latitude|longitude|"
                "event_type|sub_event_type|fatalities|notes|actor1|event_id_cnty"
            ),
        }
        cache_key = f"{self.cache_prefix}:acled_protests"
        data = await self.fetch_json(ACLED_BASE, params=params, cache_key=cache_key)
        if not data:
            return []

        records = data.get("data") or []
        events: list[dict] = []

        for rec in records:
            try:
                lat = float(rec.get("latitude", 0) or 0)
                lon = float(rec.get("longitude", 0) or 0)
            except (ValueError, TypeError):
                continue

            if lat == 0.0 and lon == 0.0:
                continue

            event_id = str(rec.get("event_id_cnty", "")) or _make_event_id(
                f"{rec.get('event_date','')}_{rec.get('country','')}_{lat}_{lon}"
            )
            country = rec.get("country", "")
            sub_event_type = rec.get("sub_event_type", "")
            notes = rec.get("notes", "")

            try:
                fatalities = int(rec.get("fatalities", 0) or 0)
            except (ValueError, TypeError):
                fatalities = 0

            # Threat from sub_event_type + notes + fatalities
            threat_text = f"{sub_event_type} {notes}"
            if fatalities > 5:
                threat = "CRITICAL"
            elif fatalities > 0:
                threat = "HIGH"
            else:
                threat = _assess_threat(threat_text)

            events.append({
                "id": event_id,
                "title": notes[:200] if notes else f"{sub_event_type} in {country}",
                "url": "",
                "source": "ACLED",
                "sourcecountry": country,
                "publishedAt": rec.get("event_date", ""),
                "image": None,
                "lat": lat,
                "lon": lon,
                "country": country,
                "threatLevel": threat,
                "eventType": rec.get("event_type", "Protests"),
                "dataSource": "ACLED",
                "language": "",
            })

        return events
