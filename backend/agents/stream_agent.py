"""
StreamAgent — provides live video stream data and imagery for protest coverage.

Sources:
  1. YouTube embed search URLs (no API key required — embed search iframes)
  2. GDELT image gallery API (free, no key required)
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote_plus

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

GDELT_DOC_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"

# YouTube search query strings for live protest coverage
_YT_SEARCH_QUERIES = [
    "protest live",
    "demonstration live news",
    "riot live stream",
    "strike news live",
    "civil unrest live",
    "march protest",
    "rally live",
    "resistance protest live",
]


def _yt_embed_url(query: str) -> str:
    """Build a YouTube embed search URL for the given query string."""
    encoded = quote_plus(query)
    return f"https://www.youtube.com/embed?listType=search&list={encoded}&autoplay=0"


class StreamAgent(BaseAgent):
    """Provides live stream embed URLs and protest imagery from GDELT."""

    cache_prefix = "stream"

    async def fetch_data(self) -> dict:
        live_streams = self._build_youtube_streams()
        images = await self._fetch_protest_images()

        return {
            "liveStreams": live_streams,
            "images": images,
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
        }

    def _build_youtube_streams(self) -> list[dict]:
        """Return a hardcoded list of YouTube embed search stream objects."""
        streams: list[dict] = []
        for idx, query in enumerate(_YT_SEARCH_QUERIES, start=1):
            streams.append({
                "id": f"yt-search-{idx}",
                "title": query.title(),
                "embedUrl": _yt_embed_url(query),
                "type": "youtube_search",
                "country": "Global",
                "thumbnail": None,
            })
        return streams

    async def _fetch_protest_images(self) -> list[dict]:
        """Fetch GDELT image gallery for recent protest imagery."""
        params = {
            "query": "protest demonstration",
            "mode": "imagegallery",
            "format": "json",
            "maxrecords": "40",
            "timespan": "6h",
        }
        cache_key = f"{self.cache_prefix}:gdelt_images"
        data = await self.fetch_json(GDELT_DOC_BASE, params=params, cache_key=cache_key)
        if not data:
            return []

        articles = data.get("articles") or []
        images: list[dict] = []

        for art in articles:
            url = art.get("url", "") or art.get("socialimage", "")
            title = art.get("title", "")
            source = art.get("domain", "") or art.get("sourcecountry", "")
            published_at = art.get("seendate", "")

            if not url:
                continue

            images.append({
                "url": url,
                "title": title,
                "source": source,
                "publishedAt": published_at,
            })

        return images
