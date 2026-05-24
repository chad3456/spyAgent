"""
Internet Outage Agent — global connectivity disruption tracking.

Sources:
1. Cloudflare Radar Outages API     (optional: CF_RADAR_TOKEN)
2. NetBlocks RSS feed               (free, no key) — civil society outage reports
3. GDELT keyword search             (fallback)

Returns recent outage events with geolocation where available.
"""

import os
import logging
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

CF_RADAR_OUTAGES = "https://api.cloudflare.com/client/v4/radar/annotations/outages"
NETBLOCKS_RSS = "https://netblocks.org/feed"

# Lightweight country centroid table for plotting outage events.
COUNTRY_CENTROIDS: dict[str, tuple[float, float]] = {
    "US": (39.83, -98.58), "RU": (61.52, 105.32), "CN": (35.86, 104.20),
    "IN": (20.59, 78.96),  "IR": (32.43, 53.69),  "IL": (31.05, 34.85),
    "UA": (48.38, 31.17),  "PK": (30.38, 69.35),  "BD": (23.68, 90.36),
    "SD": (12.86, 30.22),  "ET": (9.15, 40.49),   "MM": (21.92, 95.96),
    "EG": (26.82, 30.80),  "TR": (38.96, 35.24),  "VE": (6.42, -66.59),
    "CU": (21.52, -77.78), "AF": (33.94, 67.71),  "SY": (34.80, 38.99),
    "YE": (15.55, 48.52),  "LB": (33.85, 35.86),  "IQ": (33.22, 43.68),
    "GB": (55.38, -3.44),  "FR": (46.23, 2.21),   "DE": (51.17, 10.45),
    "BR": (-14.24, -51.93),"MX": (23.63, -102.55),"JP": (36.20, 138.25),
    "KR": (35.91, 127.77), "AU": (-25.27, 133.78),"CA": (56.13, -106.35),
}


class InternetOutageAgent(BaseAgent):
    cache_prefix = "outages"

    async def fetch_data(self) -> dict:
        outages: list[dict] = []
        sources_used: list[str] = []

        cf_token = os.environ.get("CF_RADAR_TOKEN", "").strip()
        if cf_token:
            cf_outages = await self._fetch_cloudflare(cf_token)
            outages.extend(cf_outages)
            if cf_outages:
                sources_used.append("Cloudflare Radar")

        nb_outages = await self._fetch_netblocks()
        outages.extend(nb_outages)
        if nb_outages:
            sources_used.append("NetBlocks")

        if not outages:
            news = await self.fetch_gdelt(
                "(\"internet shutdown\" OR \"network blackout\" OR \"connectivity disrupted\")",
                max_records=15,
                category="outage",
            )
            for n in news[:20]:
                outages.append({
                    "id": f"news-{hash(n['url']) & 0xffffff}",
                    "country": "",
                    "countryCode": "",
                    "lat": 0.0,
                    "lon": 0.0,
                    "title": n["title"],
                    "url": n["url"],
                    "source": n["source"],
                    "reportedAt": n.get("publishedAt", ""),
                    "type": "report",
                    "severity": "INFO",
                })
            if outages:
                sources_used.append("GDELT")

        # De-dupe by URL/title.
        seen: set[str] = set()
        deduped: list[dict] = []
        for o in outages:
            key = o.get("url") or o.get("title", "")
            if key in seen:
                continue
            seen.add(key)
            deduped.append(o)

        deduped.sort(key=lambda o: o.get("reportedAt", ""), reverse=True)

        return {
            "outages": deduped[:60],
            "summary": {
                "total": len(deduped),
                "active": sum(1 for o in deduped if o.get("type") == "active"),
                "countries": len({o["countryCode"] for o in deduped if o.get("countryCode")}),
            },
            "sources": sources_used,
            "hasCFToken": bool(cf_token),
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

    async def _fetch_cloudflare(self, token: str) -> list[dict]:
        headers = {"Authorization": f"Bearer {token}"}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(
                    CF_RADAR_OUTAGES,
                    params={"dateRange": "7d", "limit": 50},
                    headers=headers,
                )
                if r.status_code != 200:
                    return []
                data = r.json()
        except Exception as exc:
            logger.info("Cloudflare Radar unavailable: %s", exc)
            return []

        result = data.get("result", {}).get("annotations", [])
        out: list[dict] = []
        for ann in result:
            cc = (ann.get("locations") or [{}])[0].get("alpha2", "").upper()
            lat, lon = COUNTRY_CENTROIDS.get(cc, (0.0, 0.0))
            out.append({
                "id": f"cf-{ann.get('id')}",
                "country": ann.get("name", ""),
                "countryCode": cc,
                "lat": lat,
                "lon": lon,
                "title": ann.get("description", "Connectivity disruption"),
                "url": "https://radar.cloudflare.com/outages",
                "source": "Cloudflare Radar",
                "reportedAt": ann.get("startDate", ""),
                "endedAt": ann.get("endDate", ""),
                "type": "active" if not ann.get("endDate") else "resolved",
                "severity": "HIGH" if not ann.get("endDate") else "MEDIUM",
            })
        return out

    async def _fetch_netblocks(self) -> list[dict]:
        items = await self.fetch_rss(NETBLOCKS_RSS, "NetBlocks", max_items=25)
        out: list[dict] = []
        for item in items:
            title = item["title"]
            # Heuristic country detection from the title prefix.
            cc = ""
            for code, (_, _) in COUNTRY_CENTROIDS.items():
                country_name_hint = code.lower()
                if country_name_hint in title.lower():
                    cc = code
                    break
            lat, lon = COUNTRY_CENTROIDS.get(cc, (0.0, 0.0))
            out.append({
                "id": f"nb-{hash(item['url']) & 0xffffff}",
                "country": cc,
                "countryCode": cc,
                "lat": lat,
                "lon": lon,
                "title": title,
                "url": item["url"],
                "source": "NetBlocks",
                "reportedAt": item.get("publishedAt", ""),
                "type": "report",
                "severity": "HIGH",
            })
        return out
