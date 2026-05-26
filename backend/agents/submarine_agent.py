"""
Submarine Agent — submarine bases, port-of-call OSINT, and submarine news.

Real-time submarine positions are not publicly broadcast (no AIS for subs).
This agent surfaces what IS public:
  - Static map of known submarine bases (US, Russia, China, India, UK, France, etc.)
  - GDELT-derived news of recent submarine sightings, deployments, port calls
  - Naval News + USNI News RSS feeds for credible submarine activity reporting

Returns: {bases, sightings, news, summary}
"""
from __future__ import annotations


import logging
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Publicly documented submarine bases — Wikipedia / open naval references.
SUBMARINE_BASES: list[dict] = [
    # United States
    {"name": "Naval Base Kitsap (Bangor)",   "country": "US",  "lat": 47.7286, "lon": -122.7283, "type": "SSBN", "fleet": "US Pacific Fleet"},
    {"name": "Naval Submarine Base New London","country": "US","lat": 41.3905, "lon": -72.0815,  "type": "SSN",  "fleet": "US Atlantic Fleet"},
    {"name": "Naval Submarine Base Kings Bay","country": "US", "lat": 30.7935, "lon": -81.5158,  "type": "SSBN", "fleet": "US Atlantic Fleet"},
    {"name": "Naval Base Pearl Harbor",       "country": "US", "lat": 21.3499, "lon": -157.9534, "type": "SSN",  "fleet": "US Pacific Fleet"},
    {"name": "Naval Base Point Loma",         "country": "US", "lat": 32.6826, "lon": -117.2390, "type": "SSN",  "fleet": "US Pacific Fleet"},
    {"name": "Naval Base Guam",               "country": "US", "lat": 13.4419, "lon": 144.6515,  "type": "SSN",  "fleet": "US Pacific Fleet (forward)"},
    # Russia
    {"name": "Gadzhiyevo Naval Base",         "country": "RU", "lat": 69.2497, "lon": 33.3275,   "type": "SSBN", "fleet": "Northern Fleet"},
    {"name": "Vilyuchinsk Submarine Base",    "country": "RU", "lat": 52.9230, "lon": 158.4053,  "type": "SSBN", "fleet": "Pacific Fleet"},
    {"name": "Polyarny Naval Base",           "country": "RU", "lat": 69.1980, "lon": 33.4500,   "type": "SSK",  "fleet": "Northern Fleet"},
    {"name": "Sevastopol Naval Base",         "country": "RU", "lat": 44.6166, "lon": 33.5254,   "type": "SSK",  "fleet": "Black Sea Fleet"},
    # China
    {"name": "Yulin Naval Base (Hainan)",     "country": "CN", "lat": 18.2150, "lon": 109.6940,  "type": "SSBN", "fleet": "PLAN South Sea Fleet"},
    {"name": "Qingdao Submarine Base",        "country": "CN", "lat": 36.0911, "lon": 120.4691,  "type": "SSN",  "fleet": "PLAN North Sea Fleet"},
    {"name": "Jianggezhuang Naval Base",      "country": "CN", "lat": 36.1167, "lon": 120.5800,  "type": "SSBN", "fleet": "PLAN North Sea Fleet"},
    # India
    {"name": "INS Varsha (Rambilli)",         "country": "IN", "lat": 17.4970, "lon": 82.9560,   "type": "SSBN", "fleet": "Indian Navy Eastern Command"},
    {"name": "INS Virbahu (Visakhapatnam)",   "country": "IN", "lat": 17.7156, "lon": 83.3018,   "type": "SSK",  "fleet": "Indian Navy Eastern Command"},
    {"name": "INS Vajrabahu (Mumbai)",        "country": "IN", "lat": 18.9258, "lon": 72.8347,   "type": "SSK",  "fleet": "Indian Navy Western Command"},
    # United Kingdom
    {"name": "HMNB Clyde (Faslane)",          "country": "GB", "lat": 56.0670, "lon": -4.8230,   "type": "SSBN", "fleet": "Royal Navy"},
    # France
    {"name": "Île Longue Submarine Base",     "country": "FR", "lat": 48.3022, "lon": -4.5511,   "type": "SSBN", "fleet": "Marine Nationale"},
    {"name": "Toulon Naval Base",             "country": "FR", "lat": 43.1100, "lon": 5.9050,    "type": "SSN",  "fleet": "Marine Nationale"},
    # NATO / Others
    {"name": "Eckernförde (Type 212A)",       "country": "DE", "lat": 54.4660, "lon": 9.8410,    "type": "SSK",  "fleet": "Deutsche Marine"},
    {"name": "Haakonsvern Naval Base",        "country": "NO", "lat": 60.3300, "lon": 5.2400,    "type": "SSK",  "fleet": "Sjøforsvaret"},
    {"name": "Yokosuka Naval Base",           "country": "JP", "lat": 35.2916, "lon": 139.6700,  "type": "SSK",  "fleet": "JMSDF"},
    {"name": "Kure Naval Base",               "country": "JP", "lat": 34.2333, "lon": 132.5666,  "type": "SSK",  "fleet": "JMSDF"},
    {"name": "Jinhae Naval Base",             "country": "KR", "lat": 35.1444, "lon": 128.6536,  "type": "SSK",  "fleet": "Republic of Korea Navy"},
    # Iran
    {"name": "Bandar Abbas Naval Base",       "country": "IR", "lat": 27.1830, "lon": 56.2750,   "type": "SSK",  "fleet": "IRIN"},
    {"name": "Konarak Naval Base",            "country": "IR", "lat": 25.3580, "lon": 60.3960,   "type": "SSK",  "fleet": "IRIN"},
]

NAVAL_NEWS_RSS = "https://www.navalnews.com/feed/"
USNI_NEWS_RSS = "https://news.usni.org/feed"


class SubmarineAgent(BaseAgent):
    cache_prefix = "subs"

    async def fetch_data(self) -> dict:
        # Pull submarine-specific news in parallel.
        gdelt_news, naval_news, usni_news = await self._gather()

        # Filter RSS feeds down to submarine-relevant items.
        keyword_filter = ("submarine", "ssbn", "ssn", "ssk", "boomer", "u-boat", "torpedo")

        def _is_sub(item: dict) -> bool:
            blob = f"{item.get('title','')} {item.get('summary','')}".lower()
            return any(k in blob for k in keyword_filter)

        filtered_naval = [i for i in naval_news if _is_sub(i)][:10]
        filtered_usni  = [i for i in usni_news if _is_sub(i)][:10]

        sightings: list[dict] = []
        for item in gdelt_news[:25]:
            sightings.append({
                "id": f"sight-{hash(item['url']) & 0xffffff}",
                "title": item["title"],
                "url": item["url"],
                "source": item["source"],
                "publishedAt": item.get("publishedAt", ""),
            })

        return {
            "bases": SUBMARINE_BASES,
            "sightings": sightings,
            "news": {
                "navalNews": filtered_naval,
                "usni": filtered_usni,
            },
            "summary": {
                "totalBases": len(SUBMARINE_BASES),
                "countries": len({b["country"] for b in SUBMARINE_BASES}),
                "ssbnBases": sum(1 for b in SUBMARINE_BASES if b["type"] == "SSBN"),
                "recentSightings": len(sightings),
            },
            "disclaimer": (
                "Real-time submarine positions are classified and not publicly "
                "broadcast. This layer shows known base locations and OSINT-derived "
                "deployment news only."
            ),
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

    async def _gather(self):
        import asyncio
        return await asyncio.gather(
            self.fetch_gdelt(
                "submarine AND (deployed OR surfaced OR port OR launched OR drill OR patrol)",
                max_records=25,
                category="submarine",
            ),
            self.fetch_rss(NAVAL_NEWS_RSS, "Naval News", max_items=40),
            self.fetch_rss(USNI_NEWS_RSS, "USNI News", max_items=40),
            return_exceptions=False,
        )
