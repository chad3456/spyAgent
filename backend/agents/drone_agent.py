"""
Drone Agent — UAV / drone activity, strikes, and incidents.

Sources:
- GDELT news search for "drone strike", "UAV", "loitering munition", "Shahed", etc.
- Naval News + The War Zone RSS feeds
- ACLED-style hot zones (static high-activity regions)

Returns drone-related events with geolocation where extractable.
"""

import asyncio
import logging
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

WAR_ZONE_RSS = "https://www.thedrive.com/the-war-zone/feed"
DEFENSE_NEWS_RSS = "https://www.defensenews.com/arc/outboundfeeds/rss/category/unmanned/"

# Known drone-active zones — used to plot fallback points when GDELT lacks coords.
DRONE_HOTSPOTS: list[dict] = [
    {"name": "Eastern Ukraine front",     "lat": 48.0, "lon": 37.8,  "country": "UA", "tag": "shahed/lancet/bayraktar"},
    {"name": "Red Sea / Bab-el-Mandeb",   "lat": 12.5, "lon": 43.3,  "country": "YE", "tag": "houthi UAV"},
    {"name": "Gaza Strip",                "lat": 31.5, "lon": 34.5,  "country": "PS", "tag": "ISR ops"},
    {"name": "Northern Israel",           "lat": 33.0, "lon": 35.3,  "country": "IL", "tag": "hezbollah UAV"},
    {"name": "Syria/Iraq border",         "lat": 35.5, "lon": 41.0,  "country": "SY", "tag": "iranian proxy UAV"},
    {"name": "Sahel — Mali/Burkina",      "lat": 14.0, "lon": -1.0,  "country": "ML", "tag": "bayraktar TB2"},
    {"name": "Myanmar conflict zone",     "lat": 21.9, "lon": 95.9,  "country": "MM", "tag": "FPV drones"},
    {"name": "Kashmir LoC",               "lat": 34.0, "lon": 74.0,  "country": "IN", "tag": "border surveillance"},
    {"name": "Taiwan Strait",             "lat": 24.5, "lon": 120.0, "country": "TW", "tag": "PLA UAV incursions"},
    {"name": "Iran-Pakistan border",      "lat": 29.0, "lon": 61.0,  "country": "IR", "tag": "regional UAV"},
]


class DroneAgent(BaseAgent):
    cache_prefix = "drones"

    async def fetch_data(self) -> dict:
        gdelt_news, war_zone, defense_news = await asyncio.gather(
            self.fetch_gdelt(
                "(drone OR UAV OR \"loitering munition\" OR Shahed OR Bayraktar OR Switchblade) "
                "AND (strike OR attack OR intercepted OR shot OR launched OR swarm)",
                max_records=30,
                category="drone",
            ),
            self.fetch_rss(WAR_ZONE_RSS, "The War Zone", max_items=25),
            self.fetch_rss(DEFENSE_NEWS_RSS, "Defense News - Unmanned", max_items=25),
            return_exceptions=False,
        )

        kw = ("drone", "uav", "uas", "loitering munition", "shahed", "bayraktar",
              "switchblade", "lancet", "quadcopter", "fpv")

        def _is_drone(item: dict) -> bool:
            blob = f"{item.get('title','')} {item.get('summary','')}".lower()
            return any(k in blob for k in kw)

        incidents: list[dict] = []
        # GDELT — projected to hotspot centroids by best-match keyword.
        for art in gdelt_news[:25]:
            blob = art["title"].lower()
            spot = next(
                (s for s in DRONE_HOTSPOTS if any(t in blob for t in s["tag"].split() + [s["country"].lower()])),
                None,
            )
            lat, lon = (spot["lat"], spot["lon"]) if spot else (0.0, 0.0)
            incidents.append({
                "id": f"drone-{hash(art['url']) & 0xffffff}",
                "title": art["title"],
                "url": art["url"],
                "source": art["source"],
                "publishedAt": art.get("publishedAt", ""),
                "lat": lat,
                "lon": lon,
                "region": spot["name"] if spot else "Unknown",
                "tag": spot["tag"] if spot else "general",
                "severity": "HIGH" if any(w in blob for w in ("strike", "killed", "attack")) else "MEDIUM",
            })

        filtered_war_zone = [i for i in war_zone if _is_drone(i)][:10]
        filtered_defense = [i for i in defense_news if _is_drone(i)][:10]

        return {
            "incidents": incidents,
            "hotspots": DRONE_HOTSPOTS,
            "news": {
                "warZone": filtered_war_zone,
                "defense": filtered_defense,
            },
            "summary": {
                "totalIncidents": len(incidents),
                "hotspotCount": len(DRONE_HOTSPOTS),
                "highSeverity": sum(1 for i in incidents if i["severity"] == "HIGH"),
            },
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }
