"""
Salvo Agent — Iran / US (and proxy) conflict salvo tracker.

Tracks reported missile and drone exchanges between Iran, US forces in the
region, and Iranian proxies (Houthi, Hezbollah, Iraqi militias). Aggregates:
  - GDELT news searches scoped to known belligerent strings + munition keywords
  - Naval News, USNI, The War Zone RSS feeds filtered for relevant items
  - Curated salvo timeline anchors (well-documented historical exchanges)

Returns categorised salvo events with origin/target geolocation.
"""

import asyncio
import logging
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

WAR_ZONE_RSS = "https://www.thedrive.com/the-war-zone/feed"
USNI_NEWS_RSS = "https://news.usni.org/feed"
NAVAL_NEWS_RSS = "https://www.navalnews.com/feed/"
LONG_WAR_JOURNAL_RSS = "https://www.longwarjournal.org/feed"

# Well-documented salvo anchors (public, widely reported).
# Each entry is a "from -> to" pair so we can render salvo arcs on the globe.
SALVO_TIMELINE_ANCHORS: list[dict] = [
    {
        "id": "anchor-true-promise-1",
        "date": "2024-04-13",
        "name": "Operation True Promise (Iran → Israel)",
        "origin": {"name": "Iran", "lat": 32.43, "lon": 53.69},
        "target": {"name": "Israel", "lat": 31.05, "lon": 34.85},
        "munitions": "~170 Shahed UAVs, ~30 cruise missiles, ~120 ballistic missiles",
        "actor": "Iran (IRGC Aerospace Force)",
        "severity": "CRITICAL",
        "intercepted": True,
    },
    {
        "id": "anchor-true-promise-2",
        "date": "2024-10-01",
        "name": "Operation True Promise II (Iran → Israel)",
        "origin": {"name": "Iran", "lat": 32.43, "lon": 53.69},
        "target": {"name": "Israel", "lat": 31.05, "lon": 34.85},
        "munitions": "~180 ballistic missiles",
        "actor": "Iran (IRGC Aerospace Force)",
        "severity": "CRITICAL",
        "intercepted": True,
    },
    {
        "id": "anchor-tower-22",
        "date": "2024-01-28",
        "name": "Tower 22 attack (Kataib Hezbollah → US base, Jordan)",
        "origin": {"name": "Iraq (KH-aligned)", "lat": 33.31, "lon": 44.36},
        "target": {"name": "Tower 22, Jordan", "lat": 32.55, "lon": 38.20},
        "munitions": "1-way attack UAV",
        "actor": "Iranian-backed Iraqi militia",
        "severity": "CRITICAL",
        "intercepted": False,
    },
    {
        "id": "anchor-soleimani-response",
        "date": "2020-01-08",
        "name": "Operation Martyr Soleimani (Iran → Al-Asad/Erbil)",
        "origin": {"name": "Iran", "lat": 32.43, "lon": 53.69},
        "target": {"name": "Al-Asad Air Base, Iraq", "lat": 33.79, "lon": 42.44},
        "munitions": "~16 Fateh-313 / Qiam-1 ballistic missiles",
        "actor": "Iran (IRGC Aerospace Force)",
        "severity": "CRITICAL",
        "intercepted": False,
    },
    {
        "id": "anchor-houthi-redsea",
        "date": "ongoing",
        "name": "Houthi Red Sea campaign (Yemen → commercial shipping & USN)",
        "origin": {"name": "Yemen (Houthi-held)", "lat": 15.55, "lon": 48.52},
        "target": {"name": "Red Sea shipping lanes", "lat": 14.0, "lon": 42.0},
        "munitions": "Anti-ship ballistic missiles, cruise missiles, UAVs, USVs",
        "actor": "Ansar Allah (Houthi)",
        "severity": "HIGH",
        "intercepted": True,
    },
    {
        "id": "anchor-us-yemen-strikes",
        "date": "ongoing",
        "name": "US/UK strikes on Houthi positions",
        "origin": {"name": "USN CSG / Diego Garcia", "lat": 12.5, "lon": 45.0},
        "target": {"name": "Sana'a / Hodeidah, Yemen", "lat": 15.35, "lon": 44.20},
        "munitions": "Tomahawk TLAM, F/A-18 strikes, B-2 strikes",
        "actor": "US Central Command",
        "severity": "HIGH",
        "intercepted": False,
    },
]


# Iran/US-aligned actor centroids for projecting live news onto the globe.
ACTOR_CENTROIDS: dict[str, tuple[float, float]] = {
    "iran":       (32.43, 53.69),
    "tehran":     (35.69, 51.39),
    "israel":     (31.05, 34.85),
    "tel aviv":   (32.08, 34.78),
    "us base":    (24.42, 54.43),   # Al-Dhafra (UAE)
    "al asad":    (33.79, 42.44),
    "erbil":      (36.19, 44.01),
    "tower 22":   (32.55, 38.20),
    "syria":      (34.80, 38.99),
    "iraq":       (33.22, 43.68),
    "yemen":      (15.55, 48.52),
    "sanaa":      (15.35, 44.20),
    "houthi":     (15.55, 48.52),
    "hezbollah":  (33.85, 35.86),
    "lebanon":    (33.85, 35.86),
    "diego garcia":(-7.31, 72.41),
    "red sea":    (20.0, 38.0),
    "gulf of oman":(24.5, 58.5),
    "strait of hormuz":(26.57, 56.25),
}


def _locate(title: str) -> tuple[float, float, str]:
    t = title.lower()
    for k, (lat, lon) in ACTOR_CENTROIDS.items():
        if k in t:
            return lat, lon, k
    return 0.0, 0.0, ""


class SalvoAgent(BaseAgent):
    cache_prefix = "salvo"

    async def fetch_data(self) -> dict:
        gdelt_iran, gdelt_houthi, war_zone, usni, lwj = await asyncio.gather(
            self.fetch_gdelt(
                "(Iran OR IRGC OR Tehran) AND (missile OR drone OR strike OR salvo OR ballistic OR Shahed)",
                max_records=25,
                category="iran-salvo",
            ),
            self.fetch_gdelt(
                "(Houthi OR Yemen) AND (missile OR drone OR strike OR intercepted OR Red Sea)",
                max_records=20,
                category="houthi-salvo",
            ),
            self.fetch_rss(WAR_ZONE_RSS, "The War Zone", max_items=30),
            self.fetch_rss(USNI_NEWS_RSS, "USNI News", max_items=30),
            self.fetch_rss(LONG_WAR_JOURNAL_RSS, "Long War Journal", max_items=30),
            return_exceptions=False,
        )

        kw = ("iran", "irgc", "houthi", "hezbollah", "missile", "shahed",
              "ballistic", "salvo", "red sea", "tower 22", "al asad")

        def _is_salvo(item: dict) -> bool:
            blob = f"{item.get('title','')} {item.get('summary','')}".lower()
            return any(k in blob for k in kw)

        events: list[dict] = []
        for art in (gdelt_iran + gdelt_houthi)[:40]:
            lat, lon, hint = _locate(art["title"])
            events.append({
                "id": f"salvo-{hash(art['url']) & 0xffffff}",
                "title": art["title"],
                "url": art["url"],
                "source": art["source"],
                "publishedAt": art.get("publishedAt", ""),
                "lat": lat,
                "lon": lon,
                "region": hint or "unknown",
                "category": art.get("category", "salvo"),
                "severity": "HIGH" if any(w in art["title"].lower() for w in ("killed", "strike", "salvo")) else "MEDIUM",
            })

        filtered = {
            "warZone": [i for i in war_zone if _is_salvo(i)][:10],
            "usni":    [i for i in usni     if _is_salvo(i)][:10],
            "lwj":     [i for i in lwj      if _is_salvo(i)][:10],
        }

        return {
            "events": events,
            "anchors": SALVO_TIMELINE_ANCHORS,
            "news": filtered,
            "summary": {
                "totalEvents": len(events),
                "anchorEvents": len(SALVO_TIMELINE_ANCHORS),
                "criticalAnchors": sum(1 for a in SALVO_TIMELINE_ANCHORS if a["severity"] == "CRITICAL"),
            },
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }
