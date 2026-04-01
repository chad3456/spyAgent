"""
NewsAgent - Shared utility for fetching, deduplicating, and filtering news.

Used by other agents AND exposed via the /api/summary endpoint to aggregate
top headlines across all topics.
"""

import os
import logging
import asyncio
from typing import Optional

from .base_agent import BaseAgent, _now_iso, _strip_html

logger = logging.getLogger(__name__)

# RSS feed definitions: (url, friendly_name)
ECONOMIC_TIMES_MAIN = ("https://economictimes.indiatimes.com/rssfeedsdefault.cms", "Economic Times")
ECONOMIC_TIMES_MARKETS = (
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Economic Times Markets",
)
PIB_MAIN = ("https://pib.gov.in/RssMain.aspx", "PIB India")
BUSINESS_STANDARD = ("https://www.business-standard.com/rss/latest.rss", "Business Standard")

# GDELT queries: (query_string, category_tag)
GDELT_QUERIES = [
    ("india economy GDP", "economy"),
    ("india artificial intelligence data center", "ai_infra"),
    ("india road infrastructure highway", "infrastructure"),
    ("india defense military weapon", "defense"),
    ("india power renewable energy solar", "energy"),
    ("india technology startup investment", "technology"),
]


class NewsAgent(BaseAgent):
    """
    Fetches news from GDELT + RSS feeds for all topics.
    Deduplicates by title and supports keyword filtering.
    """

    cache_prefix = "news"

    def __init__(self, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self._news_api_key: Optional[str] = os.environ.get("NEWS_API_KEY", "").strip() or None
        self._gnews_api_key: Optional[str] = os.environ.get("GNEWS_API_KEY", "").strip() or None

    # ------------------------------------------------------------------
    # Public helpers used by other agents
    # ------------------------------------------------------------------

    async def fetch_rss_feeds(
        self,
        feeds: list[tuple[str, str]],
        keywords: Optional[list[str]] = None,
        max_items: int = 20,
    ) -> list[dict]:
        """
        Fetch multiple RSS feeds concurrently, optionally filter by keywords,
        and return deduplicated results.
        """
        tasks = [self.fetch_rss(url, source_name=name, max_items=max_items) for url, name in feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        combined: list[dict] = []
        for r in results:
            if isinstance(r, list):
                combined.extend(r)
            elif isinstance(r, Exception):
                logger.error("RSS fetch error: %s", r)

        if keywords:
            kw_lower = [k.lower() for k in keywords]
            combined = [
                item
                for item in combined
                if any(kw in item["title"].lower() for kw in kw_lower)
            ]

        return _deduplicate_news(combined)

    async def fetch_gdelt_multi(
        self, queries: list[tuple[str, str]], max_records: int = 10
    ) -> list[dict]:
        """
        Run multiple GDELT queries concurrently. Each tuple is (query, category).
        Returns combined deduplicated list.
        """
        tasks = [
            self.fetch_gdelt(query, max_records=max_records, category=category)
            for query, category in queries
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        combined: list[dict] = []
        for r in results:
            if isinstance(r, list):
                combined.extend(r)
            elif isinstance(r, Exception):
                logger.error("GDELT fetch error: %s", r)

        return _deduplicate_news(combined)

    async def fetch_newsapi(self, query: str, max_items: int = 10) -> list[dict]:
        """Fetch from NewsAPI if key is configured."""
        if not self._news_api_key:
            return []
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": str(max_items),
            "apiKey": self._news_api_key,
        }
        data = await self.fetch_json(url, params=params, cache_key=f"newsapi:{query}")
        if not data or data.get("status") != "ok":
            return []
        articles = data.get("articles") or []
        items = []
        for art in articles:
            title = _strip_html(art.get("title", ""))
            url_ = art.get("url", "")
            source = (art.get("source") or {}).get("name", "NewsAPI")
            published = art.get("publishedAt", "")
            if title and url_:
                items.append(
                    {"title": title, "url": url_, "source": source, "publishedAt": published}
                )
        return items

    async def fetch_gnews(self, query: str, max_items: int = 10) -> list[dict]:
        """Fetch from GNews if key is configured."""
        if not self._gnews_api_key:
            return []
        url = "https://gnews.io/api/v4/search"
        params = {
            "q": query,
            "lang": "en",
            "max": str(max_items),
            "token": self._gnews_api_key,
        }
        data = await self.fetch_json(url, params=params, cache_key=f"gnews:{query}")
        if not data:
            return []
        articles = data.get("articles") or []
        items = []
        for art in articles:
            title = _strip_html(art.get("title", ""))
            url_ = art.get("url", "")
            source = (art.get("source") or {}).get("name", "GNews")
            published = art.get("publishedAt", "")
            if title and url_:
                items.append(
                    {"title": title, "url": url_, "source": source, "publishedAt": published}
                )
        return items

    # ------------------------------------------------------------------
    # fetch_data — returns aggregated news across all topics
    # ------------------------------------------------------------------

    async def fetch_data(self) -> dict:
        """
        Aggregate top headlines across all topics for the /api/summary endpoint.
        """
        gdelt_task = self.fetch_gdelt_multi(GDELT_QUERIES, max_records=10)
        rss_task = self.fetch_rss_feeds(
            [ECONOMIC_TIMES_MAIN, ECONOMIC_TIMES_MARKETS, PIB_MAIN, BUSINESS_STANDARD],
            max_items=25,
        )
        optional_tasks = [
            self.fetch_newsapi("india economy technology defense", max_items=10),
            self.fetch_gnews("india", max_items=10),
        ]

        gdelt_news, rss_news, *optional_results = await asyncio.gather(
            gdelt_task, rss_task, *optional_tasks, return_exceptions=True
        )

        all_news: list[dict] = []
        if isinstance(gdelt_news, list):
            all_news.extend(gdelt_news)
        if isinstance(rss_news, list):
            all_news.extend(rss_news)
        for res in optional_results:
            if isinstance(res, list):
                all_news.extend(res)

        all_news = _deduplicate_news(all_news)

        return {
            "news": all_news[:50],  # top 50 across all topics
            "totalCount": len(all_news),
            "lastUpdated": _now_iso(),
        }


# ------------------------------------------------------------------
# Module-level utility
# ------------------------------------------------------------------

def _deduplicate_news(items: list[dict]) -> list[dict]:
    """
    Deduplicate news items by normalised title.
    First occurrence wins; subsequent duplicates are dropped.
    """
    seen: set[str] = set()
    unique: list[dict] = []
    for item in items:
        key = _normalise_title(item.get("title", ""))
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _normalise_title(title: str) -> str:
    """Lower-case, strip punctuation for comparison."""
    import re
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()
