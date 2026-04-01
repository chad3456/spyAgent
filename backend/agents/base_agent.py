"""
Base agent providing common utilities for all domain agents:
- Async HTTP fetch with timeout and error handling
- RSS feed parsing via feedparser + httpx
- GDELT news API wrapper
- World Bank API response parser
- Shared TTL cache
"""

import sys
import re
import html
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
import feedparser
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# Shared in-memory cache: max 256 entries, 15-minute TTL
_CACHE_TTL = 900  # 15 minutes
_shared_cache: TTLCache = TTLCache(maxsize=256, ttl=_CACHE_TTL)

GDELT_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"

# User-Agent header to reduce bot-blocking
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; IndiaProgressDashboard/1.0; "
        "+https://github.com/india-progress-dashboard)"
    ),
    "Accept": "application/json, text/html, */*",
}


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode HTML entities from a string."""
    if not text:
        return ""
    # Unescape HTML entities first
    text = html.unescape(text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


class BaseAgent(ABC):
    """
    Abstract base class for all dashboard agents.

    Subclasses must implement `fetch_data()` which returns a dict
    that will be serialised directly to the API consumer.
    """

    # Per-class TTL cache key prefix (override in subclass for namespacing)
    cache_prefix: str = "base"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._cache = _shared_cache

    # ------------------------------------------------------------------
    # Core HTTP helpers
    # ------------------------------------------------------------------

    async def fetch_json(
        self, url: str, params: Optional[dict] = None, cache_key: Optional[str] = None
    ) -> Any:
        """
        Async GET request that returns parsed JSON.

        Returns None on any error so callers can handle gracefully.
        Responses are cached by URL (+ params) for the TTL period.
        """
        key = cache_key or f"{self.cache_prefix}:json:{url}:{params}"
        if key in self._cache:
            return self._cache[key]

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=_HEADERS,
            ) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                self._cache[key] = data
                return data
        except httpx.TimeoutException:
            logger.error("Timeout fetching %s", url, file=sys.stderr)
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HTTP %s fetching %s", exc.response.status_code, url, file=sys.stderr
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Error fetching %s: %s", url, exc, file=sys.stderr)
        return None

    async def fetch_text(self, url: str, cache_key: Optional[str] = None) -> Optional[str]:
        """
        Async GET that returns raw text.  Used for RSS feeds.
        """
        key = cache_key or f"{self.cache_prefix}:text:{url}"
        if key in self._cache:
            return self._cache[key]

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=_HEADERS,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                text = response.text
                self._cache[key] = text
                return text
        except httpx.TimeoutException:
            logger.error("Timeout fetching RSS %s", url, file=sys.stderr)
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HTTP %s fetching RSS %s", exc.response.status_code, url, file=sys.stderr
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Error fetching RSS %s: %s", url, exc, file=sys.stderr)
        return None

    async def fetch_rss(
        self, url: str, source_name: str = "", max_items: int = 20
    ) -> list[dict]:
        """
        Fetch and parse an RSS/Atom feed.

        Returns a list of normalised news item dicts:
        {title, url, source, publishedAt, summary}
        """
        cache_key = f"{self.cache_prefix}:rss:{url}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        raw = await self.fetch_text(url, cache_key=f"_raw:{cache_key}")
        if not raw:
            return []

        try:
            feed = feedparser.parse(raw)
        except Exception as exc:  # noqa: BLE001
            logger.error("feedparser error for %s: %s", url, exc, file=sys.stderr)
            return []

        items: list[dict] = []
        feed_title = source_name or getattr(feed.feed, "title", url)

        for entry in feed.entries[:max_items]:
            title = _strip_html(getattr(entry, "title", ""))
            link = getattr(entry, "link", "") or getattr(entry, "id", "")
            published = ""
            if hasattr(entry, "published"):
                published = entry.published
            elif hasattr(entry, "updated"):
                published = entry.updated

            summary = _strip_html(
                getattr(entry, "summary", "")
                or getattr(entry, "description", "")
            )[:300]

            if title and link:
                items.append(
                    {
                        "title": title,
                        "url": link,
                        "source": feed_title,
                        "publishedAt": published,
                        "summary": summary,
                    }
                )

        self._cache[cache_key] = items
        return items

    async def fetch_gdelt(
        self,
        query: str,
        max_records: int = 10,
        category: str = "",
    ) -> list[dict]:
        """
        Query the GDELT Document 2.0 API for news articles.

        Returns normalised news item dicts with an optional `category` tag.
        """
        cache_key = f"{self.cache_prefix}:gdelt:{query}:{max_records}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": str(max_records),
            "sourcelang": "english",
        }

        data = await self.fetch_json(GDELT_BASE, params=params, cache_key=cache_key)
        if not data:
            return []

        articles = data.get("articles") or []
        items: list[dict] = []
        for art in articles:
            title = _strip_html(art.get("title", ""))
            url = art.get("url", "")
            source = art.get("domain", "") or art.get("sourcecountry", "")
            published = art.get("seendate", "")
            if title and url:
                item = {
                    "title": title,
                    "url": url,
                    "source": source,
                    "publishedAt": published,
                }
                if category:
                    item["category"] = category
                items.append(item)

        self._cache[cache_key] = items
        return items

    # ------------------------------------------------------------------
    # World Bank helpers
    # ------------------------------------------------------------------

    @staticmethod
    def parse_world_bank(response: Any, unit: str = "", source: str = "World Bank") -> list[dict]:
        """
        Parse World Bank API v2 response.

        Format: [metadata_dict, [{"date": "2023", "value": 123.45, ...}]]
        Returns: [{"year": int, "value": float, "unit": str, "source": str}]

        Skips entries where value is None.
        """
        if not response or not isinstance(response, list) or len(response) < 2:
            return []

        records = response[1]
        if not records:
            return []

        results: list[dict] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            raw_value = record.get("value")
            raw_date = record.get("date", "")
            if raw_value is None:
                continue
            try:
                year = int(str(raw_date)[:4])
                value = float(raw_value)
            except (ValueError, TypeError):
                continue
            entry: dict = {"year": year, "value": value, "source": source}
            if unit:
                entry["unit"] = unit
            results.append(entry)

        # Sort ascending by year
        results.sort(key=lambda x: x["year"])
        return results

    @staticmethod
    def latest_world_bank(
        response: Any, unit: str = "", source: str = "World Bank"
    ) -> Optional[dict]:
        """
        Return only the most recent non-null data point from a World Bank series.
        """
        records = BaseAgent.parse_world_bank(response, unit=unit, source=source)
        if not records:
            return None
        # records are sorted ascending; latest is last
        return records[-1]

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def fetch_data(self) -> dict:
        """
        Fetch and return all domain data.

        Must be implemented by every agent subclass.
        """
        ...
