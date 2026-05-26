"""
OSINTBlogAgent — aggregates think-tank, OSINT-investigator, and credible
defence-analysis blog feeds. Pure RSS, zero API keys, zero web-scraping —
the operators publish these feeds for exactly this kind of consumption.

Returns a deduped, time-sorted item list across all feeds plus per-source
counts.
"""

import asyncio
import logging
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Each (label, url, category). All feeds are publicly published by their
# operators and require no authentication.
OSINT_FEEDS: list[tuple[str, str, str]] = [
    # Think tanks
    ("ISW — Institute for the Study of War",       "https://www.understandingwar.org/rss.xml",                       "think-tank"),
    ("CSIS — Center for Strategic & Intl Studies", "https://www.csis.org/analysis/feed",                              "think-tank"),
    ("RUSI — Royal United Services Institute",     "https://rusi.org/explore-our-research/feed",                      "think-tank"),
    ("Atlantic Council",                            "https://www.atlanticcouncil.org/feed/",                           "think-tank"),
    ("Carnegie Endowment",                          "https://carnegieendowment.org/rss/solr",                          "think-tank"),
    ("Brookings — Foreign Policy",                  "https://www.brookings.edu/topic/foreign-policy/feed/",            "think-tank"),

    # OSINT investigators / open-source analysis
    ("Bellingcat",                                  "https://www.bellingcat.com/feed/",                                "osint"),
    ("Conflict Intelligence Team",                  "https://citeam.org/feed/",                                        "osint"),
    ("Janes Defence News",                          "https://www.janes.com/feeds/news",                                "defence"),
    ("Long War Journal",                            "https://www.longwarjournal.org/feed",                             "counter-terror"),
    ("The War Zone",                                "https://www.thedrive.com/the-war-zone/feed",                      "defence"),
    ("Naval News",                                  "https://www.navalnews.com/feed/",                                 "naval"),
    ("USNI News",                                   "https://news.usni.org/feed",                                      "naval"),
    ("Defense News",                                "https://www.defensenews.com/arc/outboundfeeds/rss/",              "defence"),
    ("Breaking Defense",                            "https://breakingdefense.com/feed/",                               "defence"),
    ("The Cipher Brief",                            "https://www.thecipherbrief.com/feed",                             "intel"),

    # Government / IGO
    ("NATO News",                                   "https://www.nato.int/cps/en/natohq/news.rss",                     "alliance"),
    ("UN News — Peace & Security",                  "https://news.un.org/feed/subscribe/en/news/topic/peace-security/feed/rss.xml", "un"),
    ("ReliefWeb Updates",                           "https://reliefweb.int/updates/rss.xml",                           "humanitarian"),

    # Cyber / infra
    ("Krebs on Security",                           "https://krebsonsecurity.com/feed/",                               "cyber"),
    ("CISA Advisories",                             "https://www.cisa.gov/cybersecurity-advisories/all.xml",           "cyber"),
]

MAX_PER_FEED = 6
MAX_TOTAL = 60


class OSINTBlogAgent(BaseAgent):
    cache_prefix = "osint_blogs"

    async def fetch_data(self) -> dict:
        # Pull all feeds in parallel. Failures degrade gracefully — we return
        # whatever succeeded along with a per-source status block.
        tasks = [
            self.fetch_rss(url, label, max_items=MAX_PER_FEED)
            for label, url, _ in OSINT_FEEDS
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        items: list[dict] = []
        per_source: dict[str, dict] = {}
        for (label, url, category), res in zip(OSINT_FEEDS, results):
            if isinstance(res, Exception):
                logger.info("OSINT blog %s failed: %s", label, res)
                per_source[label] = {"count": 0, "category": category, "url": url, "status": "error"}
                continue
            if not res:
                per_source[label] = {"count": 0, "category": category, "url": url, "status": "empty"}
                continue
            per_source[label] = {
                "count": len(res),
                "category": category,
                "url": url,
                "status": "ok",
            }
            for item in res:
                items.append({
                    "title": item.get("title", "")[:240],
                    "url": item.get("url", ""),
                    "source": label,
                    "category": category,
                    "publishedAt": item.get("publishedAt", ""),
                    "summary": (item.get("summary") or "")[:240],
                })

        # Dedupe by URL, keep newest occurrence.
        seen: set[str] = set()
        deduped: list[dict] = []
        # Sort by publishedAt descending where parseable; fall back to insertion order
        items.sort(key=lambda i: i.get("publishedAt", ""), reverse=True)
        for it in items:
            key = it["url"]
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(it)
            if len(deduped) >= MAX_TOTAL:
                break

        active = sum(1 for s in per_source.values() if s["status"] == "ok")
        return {
            "items": deduped,
            "perSource": per_source,
            "summary": {
                "totalItems": len(deduped),
                "activeSources": active,
                "totalSources": len(OSINT_FEEDS),
                "categories": sorted({c for _, _, c in OSINT_FEEDS}),
            },
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }
