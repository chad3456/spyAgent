"""
AIInfraAgent - Fetches India AI & technology infrastructure data.

Data sources:
  - GDELT: India AI / data centre / tech investment news
  - GDELT: India startup investment news
  - RSS: Economic Times (main + markets), PIB India
  - Optional: NewsAPI, GNews (via NewsAgent)
"""

import asyncio
import logging

from .base_agent import BaseAgent, _now_iso
from .news_agent import (
    NewsAgent,
    ECONOMIC_TIMES_MAIN,
    ECONOMIC_TIMES_MARKETS,
    PIB_MAIN,
    _deduplicate_news,
)

logger = logging.getLogger(__name__)

# GDELT query definitions: (query_string, category_tag)
_GDELT_QUERIES: list[tuple[str, str]] = [
    ("india artificial intelligence data center", "ai_datacenter"),
    ("india technology startup investment", "startup"),
    ("india semiconductor chip manufacturing", "semiconductor"),
    ("india digital infrastructure broadband 5G", "digital_infra"),
]

# RSS feeds relevant to AI / tech
_RSS_FEEDS = [
    ECONOMIC_TIMES_MAIN,
    ECONOMIC_TIMES_MARKETS,
    PIB_MAIN,
]

# Keywords to prefer-filter from RSS (soft filter — kept for scoring but
# all news is returned so the frontend can filter if needed)
_TECH_KEYWORDS = [
    "ai", "artificial intelligence", "data center", "startup",
    "technology", "tech", "digital", "semiconductor", "cloud",
    "broadband", "5g", "software", "it sector", "it industry",
    "investment", "unicorn", "venture", "deep tech", "quantum",
]


class AIInfraAgent(BaseAgent):
    """Agent responsible for AI & technology infrastructure news and signals."""

    cache_prefix = "ai_infra"

    def __init__(self, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self._news_agent = NewsAgent(timeout=timeout)

    async def fetch_data(self) -> dict:
        """
        Fetch all AI/tech infrastructure data in parallel.

        Returns structured JSON with categorised news items and a
        lastUpdated timestamp.
        """
        # Build individual GDELT tasks
        gdelt_tasks = [
            self.fetch_gdelt(query, max_records=10, category=category)
            for query, category in _GDELT_QUERIES
        ]

        # RSS + optional news tasks
        rss_task = self._news_agent.fetch_rss_feeds(
            _RSS_FEEDS,
            keywords=_TECH_KEYWORDS,
            max_items=25,
        )
        newsapi_task = self._news_agent.fetch_newsapi(
            "india artificial intelligence startup technology", max_items=10
        )
        gnews_task = self._news_agent.fetch_gnews(
            "india technology AI", max_items=10
        )

        # Run everything concurrently
        results = await asyncio.gather(
            *gdelt_tasks,
            rss_task,
            newsapi_task,
            gnews_task,
            return_exceptions=True,
        )

        # Separate results: first len(gdelt_tasks) are GDELT, then rss, newsapi, gnews
        n_gdelt = len(_GDELT_QUERIES)
        gdelt_results = results[:n_gdelt]
        rss_result = results[n_gdelt]
        newsapi_result = results[n_gdelt + 1]
        gnews_result = results[n_gdelt + 2]

        all_news: list[dict] = []

        # Collect GDELT results (each already has category set)
        for i, res in enumerate(gdelt_results):
            if isinstance(res, list):
                all_news.extend(res)
            elif isinstance(res, Exception):
                _, category = _GDELT_QUERIES[i]
                logger.error(
                    "GDELT fetch failed for category=%s: %s", category, res
                )

        # Collect RSS results — tag with generic "tech" category
        if isinstance(rss_result, list):
            for item in rss_result:
                if "category" not in item:
                    item["category"] = _classify_tech_category(item.get("title", ""))
            all_news.extend(rss_result)
        elif isinstance(rss_result, Exception):
            logger.error("RSS fetch failed in AIInfraAgent: %s", rss_result)

        # Collect optional NewsAPI / GNews results
        for res in (newsapi_result, gnews_result):
            if isinstance(res, list):
                for item in res:
                    if "category" not in item:
                        item["category"] = _classify_tech_category(item.get("title", ""))
                all_news.extend(res)
            elif isinstance(res, Exception):
                logger.error("Optional news fetch error in AIInfraAgent: %s", res)

        # Deduplicate
        all_news = _deduplicate_news(all_news)

        return {
            "news": all_news[:30],
            "lastUpdated": _now_iso(),
        }


def _classify_tech_category(title: str) -> str:
    """
    Heuristically classify a news title into a tech sub-category.
    Returns a string category tag.
    """
    title_lower = title.lower()
    if any(k in title_lower for k in ("artificial intelligence", " ai ", "machine learning", "deep learning", "llm", "chatgpt", "generative")):
        return "ai_datacenter"
    if any(k in title_lower for k in ("startup", "unicorn", "venture", "seed fund", "series a", "series b")):
        return "startup"
    if any(k in title_lower for k in ("semiconductor", "chip", "fab", "wafer", "tsmc")):
        return "semiconductor"
    if any(k in title_lower for k in ("broadband", "5g", "fibre", "fiber", "telecom", "data center", "cloud")):
        return "digital_infra"
    return "technology"
