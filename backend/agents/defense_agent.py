"""
DefenseAgent - Fetches India defense & military expenditure data.

Data sources:
  - World Bank: Military expenditure (% of GDP)
  - World Bank: Military expenditure (current USD)
  - GDELT: India defense / military / weapons news
  - RSS: PIB India (official government press releases)
  - Optional: NewsAPI, GNews (via NewsAgent)
"""

import asyncio
import logging

from .base_agent import BaseAgent, _now_iso
from .news_agent import (
    NewsAgent,
    PIB_MAIN,
    ECONOMIC_TIMES_MAIN,
    _deduplicate_news,
)

logger = logging.getLogger(__name__)

# World Bank indicator endpoints
WB_MIL_GDP_PERCENT = (
    "https://api.worldbank.org/v2/country/IND/indicator/MS.MIL.XPND.GD.ZS"
    "?format=json&mrv=5"
)
WB_MIL_USD = (
    "https://api.worldbank.org/v2/country/IND/indicator/MS.MIL.XPND.CD"
    "?format=json&mrv=5"
)

# GDELT query definitions: (query_string, category_tag)
_GDELT_QUERIES: list[tuple[str, str]] = [
    ("india defense military weapon procurement", "defense"),
    ("india armed forces army navy air force", "armed_forces"),
    ("india missile drone technology DRDO", "technology"),
    ("india border security geopolitics strategic", "geopolitics"),
]

# RSS feeds for defense news
_RSS_FEEDS = [
    PIB_MAIN,
    ECONOMIC_TIMES_MAIN,
]

# Keywords to filter RSS items for defense relevance
_DEFENSE_KEYWORDS = [
    "defense", "defence", "military", "army", "navy", "air force",
    "weapon", "missile", "drone", "drdo", "hal", "bharat electronics",
    "security", "border", "strategic", "nuclear", "armed forces",
    "soldier", "war", "conflict", "geopolitics", "procurement",
    "indigenisation", "make in india defense",
]


class DefenseAgent(BaseAgent):
    """Agent responsible for defense and military expenditure data."""

    cache_prefix = "defense"

    def __init__(self, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self._news_agent = NewsAgent(timeout=timeout)

    async def fetch_data(self) -> dict:
        """
        Fetch all defense data in parallel.

        Returns:
          - militaryExpenditure: time-series of military spending in USD Billions
          - militaryGdpPercent: time-series of military spending as % of GDP
          - news: recent defense & security news
          - lastUpdated: ISO timestamp
        """
        gdelt_tasks = [
            self.fetch_gdelt(query, max_records=10, category=category)
            for query, category in _GDELT_QUERIES
        ]

        rss_task = self._news_agent.fetch_rss_feeds(
            _RSS_FEEDS,
            keywords=_DEFENSE_KEYWORDS,
            max_items=25,
        )
        newsapi_task = self._news_agent.fetch_newsapi(
            "india defense military security", max_items=10
        )
        gnews_task = self._news_agent.fetch_gnews(
            "india defense military", max_items=10
        )

        # Run all fetches concurrently
        results = await asyncio.gather(
            self.fetch_json(WB_MIL_GDP_PERCENT),
            self.fetch_json(WB_MIL_USD),
            *gdelt_tasks,
            rss_task,
            newsapi_task,
            gnews_task,
            return_exceptions=True,
        )

        # Unpack results
        wb_gdp_pct_raw = results[0]
        wb_usd_raw = results[1]
        n_gdelt = len(_GDELT_QUERIES)
        gdelt_results = results[2: 2 + n_gdelt]
        rss_result = results[2 + n_gdelt]
        newsapi_result = results[2 + n_gdelt + 1]
        gnews_result = results[2 + n_gdelt + 2]

        # --- World Bank: Military expenditure % of GDP ---
        military_gdp_percent: list[dict] = []
        if not isinstance(wb_gdp_pct_raw, Exception):
            raw = self.parse_world_bank(
                wb_gdp_pct_raw,
                unit="% of GDP",
                source="World Bank",
            )
            for entry in raw:
                military_gdp_percent.append(
                    {
                        "year": entry["year"],
                        "value": round(entry["value"], 3),
                        "unit": "% of GDP",
                        "source": "World Bank",
                    }
                )
        else:
            logger.error(
                "World Bank military GDP% fetch failed: %s", wb_gdp_pct_raw
            )

        # --- World Bank: Military expenditure (USD) converted to USD Billions ---
        military_expenditure: list[dict] = []
        if not isinstance(wb_usd_raw, Exception):
            raw = self.parse_world_bank(
                wb_usd_raw,
                unit="USD",
                source="World Bank",
            )
            for entry in raw:
                military_expenditure.append(
                    {
                        "year": entry["year"],
                        "value": round(entry["value"] / 1e9, 3),
                        "unit": "USD Billion",
                        "source": "World Bank",
                    }
                )
        else:
            logger.error(
                "World Bank military USD fetch failed: %s", wb_usd_raw
            )

        # --- News aggregation ---
        all_news: list[dict] = []

        for i, res in enumerate(gdelt_results):
            if isinstance(res, list):
                all_news.extend(res)
            elif isinstance(res, Exception):
                _, category = _GDELT_QUERIES[i]
                logger.error(
                    "GDELT fetch failed for category=%s: %s", category, res
                )

        if isinstance(rss_result, list):
            all_news.extend(rss_result)
        elif isinstance(rss_result, Exception):
            logger.error("RSS fetch failed in DefenseAgent: %s", rss_result)

        for res in (newsapi_result, gnews_result):
            if isinstance(res, list):
                all_news.extend(res)
            elif isinstance(res, Exception):
                logger.error("Optional news error in DefenseAgent: %s", res)

        all_news = _deduplicate_news(all_news)

        return {
            "militaryExpenditure": military_expenditure,
            "militaryGdpPercent": military_gdp_percent,
            "news": all_news[:30],
            "lastUpdated": _now_iso(),
        }
