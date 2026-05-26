"""
Social Media Agent — geopolitical intelligence from verified social media accounts.

Source priority:
1. Twitter/X API v2 Recent Search (requires TWITTER_BEARER_TOKEN env var)
2. GDELT Document API for social media share signals
3. RSS feeds from verified news organisations as final fallback

Curated list of verified OSINT/geopolitics accounts to track.

Returns:
  {feeds, summary}
"""
from __future__ import annotations


import asyncio
import hashlib
import logging
import os
import re
from datetime import datetime, timezone

from .base_agent import BaseAgent, _strip_html

logger = logging.getLogger(__name__)

TWITTER_SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"

VERIFIED_ACCOUNTS = [
    "Reuters", "AP", "BBC", "CNN", "AlJazeera",
    "nytimes", "guardian", "washingtonpost",
    "TheEconomist", "ForeignPolicy",
    "NATO", "UN", "StateDept", "Pentagon_Press",
    "ISW_Research", "conflictmonitor", "OSINTdefender",
    "IntelCrab", "WarMonitor3", "ArmedForcesPress",
    "UAWeapons", "DefenceHQ", "IDF", "KyivIndependent",
    "ROG_Intelligence", "ELINT_News", "GeoConfirmed",
]

GEOPOLITICAL_KEYWORDS = [
    "geopolitics", "defense", "war", "conflict", "military",
    "NATO", "sanctions", "airstrike", "offensive", "ceasefire",
    "invasion", "missile", "troops", "OSINT",
]

# RSS fallback feeds for OSINT/geopolitics
RSS_FALLBACK_FEEDS = [
    ("http://feeds.reuters.com/reuters/worldnews", "Reuters World"),
    ("http://feeds.bbci.co.uk/news/world/rss.xml", "BBC World"),
    ("https://www.aljazeera.com/xml/rss/all.xml", "Al Jazeera"),
    ("https://www.defensenews.com/rss/", "Defense News"),
    ("https://breakingdefense.com/feed/", "Breaking Defense"),
    ("https://warontherocks.com/feed/", "War on the Rocks"),
    ("https://www.bellingcat.com/feed/", "Bellingcat"),
]

# Topic keyword mapping for classification
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "war": ["war", "battle", "combat", "airstrike", "bombardment", "troops", "invasion", "offensive"],
    "geopolitics": ["geopolitics", "diplomatic", "sanctions", "treaty", "summit", "alliance", "NATO"],
    "conflict": ["conflict", "ceasefire", "protest", "uprising", "unrest", "clashes", "violence"],
    "cyber": ["cyber", "hack", "ransomware", "malware", "breach", "DDoS", "espionage"],
    "military": ["military", "defense", "army", "navy", "air force", "weapon", "missile", "drone"],
}


def _classify_topics(text: str) -> list[str]:
    lower = text.lower()
    topics = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            topics.append(topic)
    return topics or ["general"]


def _make_id(prefix: str, content: str) -> str:
    return f"{prefix}-{hashlib.md5(content.encode()).hexdigest()[:10]}"


class SocialMediaAgent(BaseAgent):
    cache_prefix = "social_feeds"

    def __init__(self, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self._twitter_token = os.getenv("TWITTER_BEARER_TOKEN", "").strip() or None

    # ------------------------------------------------------------------
    # Twitter/X API v2
    # ------------------------------------------------------------------
    async def _fetch_twitter(self) -> list[dict]:
        if not self._twitter_token:
            return []

        # Build from: filter with verified accounts
        from_clause = " OR ".join(f"from:{a}" for a in VERIFIED_ACCOUNTS[:20])
        query = f"({from_clause}) ({' OR '.join(GEOPOLITICAL_KEYWORDS[:8])}) lang:en -is:retweet"

        params = {
            "query": query[:512],  # Twitter query max 512 chars
            "max_results": "100",
            "tweet.fields": "created_at,author_id,entities,geo,public_metrics",
            "expansions": "author_id",
            "user.fields": "name,username,verified",
        }

        try:
            import httpx
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(
                    TWITTER_SEARCH_URL,
                    params=params,
                    headers={
                        "Authorization": f"Bearer {self._twitter_token}",
                        "Accept": "application/json",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.warning("Twitter API failed: %s", exc)
            return []

        tweets = data.get("data") or []
        users_by_id: dict[str, dict] = {}
        for user in (data.get("includes", {}) or {}).get("users", []):
            users_by_id[user["id"]] = user

        feeds = []
        for tweet in tweets:
            author_id = tweet.get("author_id", "")
            user = users_by_id.get(author_id, {})
            username = user.get("username", "unknown")
            name = user.get("name", username)
            verified = user.get("verified", False)

            text = tweet.get("text", "")
            created = tweet.get("created_at", "")
            tweet_id = tweet.get("id", "")
            url = f"https://twitter.com/{username}/status/{tweet_id}"

            topics = _classify_topics(text)

            feeds.append({
                "id": tweet_id,
                "author": name,
                "handle": username,
                "content": text,
                "url": url,
                "publishedAt": created,
                "platform": "twitter",
                "topic": topics[0] if topics else "general",
                "topics": topics,
                "lat": None,
                "lon": None,
                "verified": verified,
                "metrics": tweet.get("public_metrics"),
            })
        return feeds

    # ------------------------------------------------------------------
    # GDELT social share signals
    # ------------------------------------------------------------------
    async def _fetch_gdelt_social(self) -> list[dict]:
        queries = [
            ("war military conflict NATO sanctions", "geopolitics"),
            ("cyberattack hacker espionage intelligence", "cyber"),
            ("airstrike offensive ceasefire troops", "war"),
        ]
        tasks = [
            self.fetch_gdelt(q, max_records=15, category=cat)
            for q, cat in queries
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        feeds = []
        for batch in results:
            if isinstance(batch, Exception):
                continue
            for art in batch:
                title = art.get("title", "")
                url = art.get("url", "")
                if not title or not url:
                    continue
                topics = _classify_topics(title)
                feeds.append({
                    "id": _make_id("gdelt", url),
                    "author": art.get("source", "GDELT"),
                    "handle": None,
                    "content": title,
                    "url": url,
                    "publishedAt": art.get("publishedAt", ""),
                    "platform": "gdelt",
                    "topic": art.get("category", topics[0] if topics else "general"),
                    "topics": topics,
                    "lat": None,
                    "lon": None,
                    "verified": True,
                    "metrics": None,
                })
        return feeds

    # ------------------------------------------------------------------
    # RSS fallback
    # ------------------------------------------------------------------
    async def _fetch_rss_fallback(self) -> list[dict]:
        tasks = [
            self.fetch_rss(url, source_name=name, max_items=15)
            for url, name in RSS_FALLBACK_FEEDS
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        feeds = []
        for batch in results:
            if isinstance(batch, Exception):
                continue
            for item in batch:
                title = item.get("title", "")
                url = item.get("url", "")
                if not title or not url:
                    continue
                topics = _classify_topics(title)
                if not topics or topics == ["general"]:
                    # Only include geopolitically relevant articles
                    pass  # include all RSS items from these curated feeds
                feeds.append({
                    "id": _make_id("rss", url),
                    "author": item.get("source", "RSS"),
                    "handle": None,
                    "content": title,
                    "url": url,
                    "publishedAt": item.get("publishedAt", ""),
                    "platform": "rss",
                    "topic": topics[0] if topics else "general",
                    "topics": topics,
                    "lat": None,
                    "lon": None,
                    "verified": True,
                    "metrics": None,
                })
        return feeds

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    async def fetch_data(self) -> dict:
        cache_key = f"{self.cache_prefix}:all"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        twitter_task = self._fetch_twitter()
        gdelt_task = self._fetch_gdelt_social()
        rss_task = self._fetch_rss_fallback()

        twitter_feeds, gdelt_feeds, rss_feeds = await asyncio.gather(
            twitter_task, gdelt_task, rss_task,
            return_exceptions=False,
        )

        # Merge: prefer Twitter, then GDELT, then RSS (dedup by URL)
        seen_urls: set[str] = set()
        all_feeds: list[dict] = []

        for batch in (twitter_feeds, gdelt_feeds, rss_feeds):
            if isinstance(batch, Exception):
                continue
            for item in batch:
                url = item.get("url", "")
                if url in seen_urls:
                    continue
                if url:
                    seen_urls.add(url)
                all_feeds.append(item)

        # Sort most recent first
        def _parse_time(item: dict) -> str:
            return item.get("publishedAt") or ""

        all_feeds.sort(key=_parse_time, reverse=True)

        # Build topic summary
        topic_counts: dict[str, int] = {}
        for item in all_feeds:
            for t in (item.get("topics") or [item.get("topic", "general")]):
                topic_counts[t] = topic_counts.get(t, 0) + 1

        result = {
            "feeds": all_feeds[:200],
            "summary": {
                "totalPosts": len(all_feeds),
                "topics": topic_counts,
                "hasTwitter": self._twitter_token is not None,
                "sources": list({f.get("platform") for f in all_feeds}),
            },
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

        self._cache[cache_key] = result
        return result
