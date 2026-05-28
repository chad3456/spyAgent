"""
InfrastructureAgent - Fetches India physical infrastructure data.

Data sources:
  - World Bank: Electric power consumption (kWh per capita)
  - World Bank: Renewable energy share (% of total final energy)
  - GDELT: India road/highway infrastructure news
  - GDELT: India power/renewable energy/solar news
  - RSS: PIB India (official government press releases)
  - Optional: NewsAPI, GNews (via NewsAgent)
"""
from __future__ import annotations


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
WB_ELECTRIC_POWER = (
    "https://api.worldbank.org/v2/country/IND/indicator/EG.USE.ELEC.KH.PC"
    "?format=json&mrv=5"
)
WB_RENEWABLE = (
    "https://api.worldbank.org/v2/country/IND/indicator/EG.FEC.RNEW.ZS"
    "?format=json&mrv=5"
)

# GDELT queries: (query_string, category_tag)
_GDELT_QUERIES: list[tuple[str, str]] = [
    ("india road infrastructure highway expressway", "roads"),
    ("india power renewable energy solar wind", "energy"),
    ("india railway rail metro urban transit", "railways"),
    ("india port airport logistics infrastructure", "logistics"),
]

# RSS feeds for infrastructure
_RSS_FEEDS = [
    PIB_MAIN,
    ECONOMIC_TIMES_MAIN,
]

# Infrastructure-related keywords for RSS filtering
_INFRA_KEYWORDS = [
    "road", "highway", "expressway", "bridge",
    "rail", "railway", "metro", "train",
    "airport", "port", "logistics", "warehouse",
    "power", "electricity", "solar", "wind", "renewable",
    "energy", "grid", "transmission", "distribution",
    "water", "dam", "irrigation", "pipeline",
    "smart city", "urban", "infra", "infrastructure",
    "construction", "project", "corridor",
]


class InfrastructureAgent(BaseAgent):
    """Agent responsible for physical infrastructure data."""

    cache_prefix = "infrastructure"

    def __init__(self, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self._news_agent = NewsAgent(timeout=timeout)

    async def fetch_data(self) -> dict:
        """
        Fetch all infrastructure data in parallel.

        Returns:
          - power: time-series of electric power consumption per capita
          - renewable: time-series of renewable energy share
          - news: recent infrastructure news articles with category tags
          - lastUpdated: ISO timestamp
        """
        gdelt_tasks = [
            self.fetch_gdelt(query, max_records=10, category=category)
            for query, category in _GDELT_QUERIES
        ]

        rss_task = self._news_agent.fetch_rss_feeds(
            _RSS_FEEDS,
            keywords=_INFRA_KEYWORDS,
            max_items=25,
        )
        newsapi_task = self._news_agent.fetch_newsapi(
            "india infrastructure road power energy", max_items=10
        )
        gnews_task = self._news_agent.fetch_gnews(
            "india infrastructure energy", max_items=10
        )

        # Run everything concurrently
        results = await asyncio.gather(
            self.fetch_json(WB_ELECTRIC_POWER),
            self.fetch_json(WB_RENEWABLE),
            *gdelt_tasks,
            rss_task,
            newsapi_task,
            gnews_task,
            return_exceptions=True,
        )

        # Unpack results
        wb_power_raw = results[0]
        wb_renewable_raw = results[1]
        n_gdelt = len(_GDELT_QUERIES)
        gdelt_results = results[2: 2 + n_gdelt]
        rss_result = results[2 + n_gdelt]
        newsapi_result = results[2 + n_gdelt + 1]
        gnews_result = results[2 + n_gdelt + 2]

        # --- World Bank: Power consumption series ---
        power_series: list[dict] = []
        if not isinstance(wb_power_raw, Exception):
            raw = self.parse_world_bank(
                wb_power_raw,
                unit="kWh per capita",
                source="World Bank",
            )
            for entry in raw:
                power_series.append(
                    {
                        "year": entry["year"],
                        "value": round(entry["value"], 2),
                        "indicator": "Electric Power Consumption",
                        "unit": "kWh per capita",
                        "source": "World Bank",
                    }
                )
        else:
            logger.error("World Bank electric power fetch failed: %s", wb_power_raw)

        # --- World Bank: Renewable energy share series ---
        renewable_series: list[dict] = []
        if not isinstance(wb_renewable_raw, Exception):
            raw = self.parse_world_bank(
                wb_renewable_raw,
                unit="% of total final energy",
                source="World Bank",
            )
            for entry in raw:
                renewable_series.append(
                    {
                        "year": entry["year"],
                        "value": round(entry["value"], 2),
                        "unit": "% of total final energy",
                        "source": "World Bank",
                    }
                )
        else:
            logger.error("World Bank renewable energy fetch failed: %s", wb_renewable_raw)

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
            for item in rss_result:
                if "category" not in item:
                    item["category"] = _classify_infra_category(item.get("title", ""))
            all_news.extend(rss_result)
        elif isinstance(rss_result, Exception):
            logger.error("RSS fetch failed in InfrastructureAgent: %s", rss_result)

        for res in (newsapi_result, gnews_result):
            if isinstance(res, list):
                for item in res:
                    if "category" not in item:
                        item["category"] = _classify_infra_category(item.get("title", ""))
                all_news.extend(res)
            elif isinstance(res, Exception):
                logger.error("Optional news error in InfrastructureAgent: %s", res)

        all_news = _deduplicate_news(all_news)

        return {
            "power": power_series,
            "renewable": renewable_series,
            "news": all_news[:30],
            "lastUpdated": _now_iso(),
        }


def _classify_infra_category(title: str) -> str:
    """Classify infrastructure news article into a sub-category."""
    title_lower = title.lower()
    if any(k in title_lower for k in ("solar", "wind", "renewable", "power", "energy", "grid", "electricity", "hydro")):
        return "energy"
    if any(k in title_lower for k in ("road", "highway", "expressway", "bridge", "tunnel")):
        return "roads"
    if any(k in title_lower for k in ("rail", "railway", "metro", "train", "bullet", "freight")):
        return "railways"
    if any(k in title_lower for k in ("airport", "port", "logistics", "shipping", "cargo")):
        return "logistics"
    if any(k in title_lower for k in ("water", "dam", "irrigation", "flood", "pipeline")):
        return "water"
    return "infrastructure"
