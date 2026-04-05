"""
News Intel Agent — aggregated intelligence and geopolitical news.

Sources (in priority order):
1. NewsAPI (requires NEWS_API_KEY env var) — topic-filtered recent articles
2. RSS feeds from defence/intelligence media outlets
3. GDELT Document API — broad geopolitical query coverage

Topics tracked: geopolitics, defense, war, military, cyberattack, sanctions, NATO, conflict

Returns:
  {articles, categories, summary}
"""

import asyncio
import hashlib
import logging
import os
from datetime import datetime, timezone

from .base_agent import BaseAgent, _strip_html

logger = logging.getLogger(__name__)

NEWSAPI_URL = "https://newsapi.org/v2/everything"

NEWSAPI_TOPICS: list[tuple[str, str]] = [
    ("geopolitics OR diplomacy OR sanctions OR NATO", "geopolitics"),
    ("war OR military offensive OR airstrike OR troops", "war"),
    ("cyberattack OR cyber espionage OR ransomware OR hacker", "cyber"),
    ("defense budget OR arms deal OR weapons system OR missile", "defense"),
    ("conflict OR ceasefire OR insurgency OR rebel OR coup", "conflict"),
]

RSS_FEEDS: list[tuple[str, str]] = [
    ("http://feeds.reuters.com/reuters/worldnews", "Reuters World"),
    ("http://feeds.bbci.co.uk/news/world/rss.xml", "BBC World"),
    ("https://www.aljazeera.com/xml/rss/all.xml", "Al Jazeera"),
    ("https://www.defensenews.com/rss/", "Defense News"),
    ("https://breakingdefense.com/feed/", "Breaking Defense"),
    ("https://warontherocks.com/feed/", "War on the Rocks"),
    ("https://www.bellingcat.com/feed/", "Bellingcat"),
    ("https://theintercept.com/feed/?rss", "The Intercept"),
    ("https://foreignpolicy.com/feed/", "Foreign Policy"),
]

GDELT_QUERIES: list[tuple[str, str]] = [
    ("geopolitics NATO military sanctions", "geopolitics"),
    ("war conflict airstrike troops invasion", "war"),
    ("cyberattack espionage hacking malware", "cyber"),
    ("defense weapons missile drone military", "defense"),
    ("ceasefire peace talks diplomacy summit", "geopolitics"),
]

# Category keyword classifier
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "geopolitics": ["geopolitic", "diplomatic", "sanction", "nato", "treaty", "summit", "alliance", "un council"],
    "war": ["war", "battle", "airstrike", "offensive", "troops", "invasion", "bombardment", "shelling"],
    "cyber": ["cyber", "hack", "ransomware", "malware", "data breach", "ddos", "espionage", "phishing"],
    "defense": ["defense", "military", "weapon", "missile", "drone", "aircraft", "navy", "army", "nuclear"],
    "conflict": ["conflict", "protest", "unrest", "clashes", "ceasefire", "insurgency", "rebel", "coup"],
}


def _categorize(title: str, description: str = "") -> str:
    text = (title + " " + description).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "general"


def _make_id(prefix: str, url: str) -> str:
    return f"{prefix}-{hashlib.md5(url.encode()).hexdigest()[:10]}"


class NewsIntelAgent(BaseAgent):
    cache_prefix = "news_intel"

    def __init__(self, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self._news_api_key = os.getenv("NEWS_API_KEY", "").strip() or None

    # ------------------------------------------------------------------
    # NewsAPI
    # ------------------------------------------------------------------
    async def _fetch_newsapi_topic(self, query: str, category: str) -> list[dict]:
        if not self._news_api_key:
            return []
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": "20",
            "apiKey": self._news_api_key,
        }
        data = await self.fetch_json(
            NEWSAPI_URL,
            params=params,
            cache_key=f"{self.cache_prefix}:newsapi:{category}",
        )
        if not data or data.get("status") != "ok":
            return []

        articles = []
        for art in (data.get("articles") or []):
            title = _strip_html(art.get("title") or "")
            url = art.get("url", "")
            if not title or not url or title == "[Removed]":
                continue
            source_obj = art.get("source") or {}
            source = source_obj.get("name", "NewsAPI")
            description = _strip_html(art.get("description") or "")[:300]
            articles.append({
                "id": _make_id("na", url),
                "title": title,
                "source": source,
                "url": url,
                "publishedAt": art.get("publishedAt", ""),
                "description": description,
                "category": category,
                "country": None,
                "lat": None,
                "lon": None,
            })
        return articles

    async def _fetch_all_newsapi(self) -> list[dict]:
        if not self._news_api_key:
            return []
        tasks = [
            self._fetch_newsapi_topic(query, category)
            for query, category in NEWSAPI_TOPICS
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        combined = []
        for batch in results:
            if isinstance(batch, list):
                combined.extend(batch)
        return combined

    # ------------------------------------------------------------------
    # RSS feeds
    # ------------------------------------------------------------------
    async def _fetch_all_rss(self) -> list[dict]:
        tasks = [
            self.fetch_rss(url, source_name=name, max_items=20)
            for url, name in RSS_FEEDS
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        for batch in results:
            if isinstance(batch, Exception):
                continue
            for item in batch:
                title = item.get("title", "")
                url = item.get("url", "")
                if not title or not url:
                    continue
                description = item.get("summary", "")
                category = _categorize(title, description)
                articles.append({
                    "id": _make_id("rss", url),
                    "title": title,
                    "source": item.get("source", "RSS"),
                    "url": url,
                    "publishedAt": item.get("publishedAt", ""),
                    "description": description[:300],
                    "category": category,
                    "country": None,
                    "lat": None,
                    "lon": None,
                })
        return articles

    # ------------------------------------------------------------------
    # GDELT
    # ------------------------------------------------------------------
    async def _fetch_all_gdelt(self) -> list[dict]:
        tasks = [
            self.fetch_gdelt(query, max_records=15, category=category)
            for query, category in GDELT_QUERIES
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        for batch in results:
            if isinstance(batch, Exception):
                continue
            for art in batch:
                title = art.get("title", "")
                url = art.get("url", "")
                if not title or not url:
                    continue
                articles.append({
                    "id": _make_id("gd", url),
                    "title": title,
                    "source": art.get("source", "GDELT"),
                    "url": url,
                    "publishedAt": art.get("publishedAt", ""),
                    "description": "",
                    "category": art.get("category", "general"),
                    "country": None,
                    "lat": None,
                    "lon": None,
                })
        return articles

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    async def fetch_data(self) -> dict:
        cache_key = f"{self.cache_prefix}:all"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        newsapi_task = self._fetch_all_newsapi()
        rss_task = self._fetch_all_rss()
        gdelt_task = self._fetch_all_gdelt()

        newsapi_articles, rss_articles, gdelt_articles = await asyncio.gather(
            newsapi_task, rss_task, gdelt_task,
            return_exceptions=False,
        )

        # Merge: NewsAPI first (most structured), then RSS, then GDELT
        seen_urls: set[str] = set()
        all_articles: list[dict] = []

        for batch in (newsapi_articles, rss_articles, gdelt_articles):
            if isinstance(batch, Exception):
                continue
            for item in batch:
                url = item.get("url", "")
                if url in seen_urls:
                    continue
                if url:
                    seen_urls.add(url)
                all_articles.append(item)

        # Sort by publishedAt descending
        all_articles.sort(key=lambda x: x.get("publishedAt") or "", reverse=True)

        # Build category buckets
        categories: dict[str, list[dict]] = {
            "geopolitics": [],
            "war": [],
            "cyber": [],
            "defense": [],
            "conflict": [],
            "general": [],
        }
        for art in all_articles:
            cat = art.get("category", "general")
            if cat not in categories:
                categories["general"].append(art)
            else:
                categories[cat].append(art)

        unique_sources = list({a.get("source", "") for a in all_articles if a.get("source")})

        result = {
            "articles": all_articles[:150],
            "categories": {k: v[:30] for k, v in categories.items()},
            "summary": {
                "totalArticles": len(all_articles),
                "sources": unique_sources[:50],
                "hasNewsAPI": self._news_api_key is not None,
                "lastUpdated": datetime.now(timezone.utc).isoformat(),
            },
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

        self._cache[cache_key] = result
        return result
