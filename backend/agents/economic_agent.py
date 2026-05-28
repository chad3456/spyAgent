"""
EconomicAgent - Fetches India macroeconomic data.

Data sources:
  - World Bank Open API (GDP, growth, FDI, inflation, exports, manufacturing, ease-of-doing-business)
  - IMF DataMapper API (real GDP growth projections)
  - GDELT (economy/GDP news)
  - RSS: Economic Times, Business Standard
  - Optional: NewsAPI, GNews
"""
from __future__ import annotations


import asyncio
import logging
from typing import Any

from .base_agent import BaseAgent, _now_iso
from .news_agent import NewsAgent, ECONOMIC_TIMES_MAIN, ECONOMIC_TIMES_MARKETS, BUSINESS_STANDARD

logger = logging.getLogger(__name__)

# World Bank indicator URLs
WB_GDP = (
    "https://api.worldbank.org/v2/country/IND/indicator/NY.GDP.MKTP.CD"
    "?format=json&mrv=5"
)
WB_GDP_GROWTH = (
    "https://api.worldbank.org/v2/country/IND/indicator/NY.GDP.MKTP.KD.ZG"
    "?format=json&mrv=5"
)
WB_FDI = (
    "https://api.worldbank.org/v2/country/IND/indicator/BX.KLT.DINV.WD.GD.ZS"
    "?format=json&mrv=5"
)
WB_MANUFACTURING = (
    "https://api.worldbank.org/v2/country/IND/indicator/NV.IND.MANF.ZS"
    "?format=json&mrv=5"
)
WB_INFLATION = (
    "https://api.worldbank.org/v2/country/IND/indicator/FP.CPI.TOTL.ZG"
    "?format=json&mrv=5"
)
WB_EXPORTS = (
    "https://api.worldbank.org/v2/country/IND/indicator/NE.EXP.GNFS.ZS"
    "?format=json&mrv=5"
)
WB_EASE_BUSINESS = (
    "https://api.worldbank.org/v2/country/IND/indicator/IC.BUS.EASE.XQ"
    "?format=json&mrv=5"
)

# IMF DataMapper API
IMF_GDP_GROWTH = (
    "https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH/IND"
    "?periods=2020,2021,2022,2023,2024"
)
IMF_INFLATION = (
    "https://www.imf.org/external/datamapper/api/v1/PCPIPCH/IND"
    "?periods=2020,2021,2022,2023,2024"
)


def _parse_imf(response: Any, indicator: str) -> list[dict]:
    """
    Parse IMF DataMapper response for a given indicator and country (IND).

    Response shape:
    {
      "values": {
        "<INDICATOR>": {
          "IND": {
            "2020": 4.0,
            "2021": 8.9,
            ...
          }
        }
      }
    }
    Returns: [{"year": int, "value": float, "source": "IMF"}]
    """
    if not response or not isinstance(response, dict):
        return []

    try:
        country_data: dict = response["values"][indicator]["IND"]
    except (KeyError, TypeError):
        return []

    results = []
    for year_str, value in country_data.items():
        if value is None:
            continue
        try:
            results.append({"year": int(year_str), "value": float(value), "source": "IMF"})
        except (ValueError, TypeError):
            continue

    results.sort(key=lambda x: x["year"])
    return results


class EconomicAgent(BaseAgent):
    """Agent responsible for all macroeconomic indicators."""

    cache_prefix = "economic"

    def __init__(self, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self._news_agent = NewsAgent(timeout=timeout)

    async def fetch_data(self) -> dict:
        """
        Fetch all economic data in parallel and return structured response.
        """
        (
            wb_gdp_raw,
            wb_growth_raw,
            wb_fdi_raw,
            wb_inflation_raw,
            wb_exports_raw,
            wb_manufacturing_raw,
            wb_ease_raw,
            imf_growth_raw,
            imf_inflation_raw,
            gdelt_news,
            rss_news,
        ) = await asyncio.gather(
            self.fetch_json(WB_GDP),
            self.fetch_json(WB_GDP_GROWTH),
            self.fetch_json(WB_FDI),
            self.fetch_json(WB_INFLATION),
            self.fetch_json(WB_EXPORTS),
            self.fetch_json(WB_MANUFACTURING),
            self.fetch_json(WB_EASE_BUSINESS),
            self.fetch_json(IMF_GDP_GROWTH),
            self.fetch_json(IMF_INFLATION),
            self.fetch_gdelt("india economy GDP", max_records=10, category="economy"),
            self._news_agent.fetch_rss_feeds(
                [ECONOMIC_TIMES_MAIN, ECONOMIC_TIMES_MARKETS, BUSINESS_STANDARD],
                max_items=20,
            ),
            return_exceptions=True,
        )

        # --- GDP (latest value, convert to USD Billions) ---
        gdp_entry = None
        if not isinstance(wb_gdp_raw, Exception):
            latest = self.latest_world_bank(wb_gdp_raw, unit="USD", source="World Bank")
            if latest:
                gdp_entry = {
                    "value": round(latest["value"] / 1e9, 2),
                    "year": latest["year"],
                    "unit": "USD Billion",
                    "source": "World Bank",
                }

        # --- GDP Growth series ---
        gdp_growth_series: list[dict] = []
        if not isinstance(wb_growth_raw, Exception):
            gdp_growth_series = self.parse_world_bank(
                wb_growth_raw, unit="%", source="World Bank"
            )

        # Merge with IMF projections (IMF fills more recent years)
        imf_growth_series: list[dict] = []
        if not isinstance(imf_growth_raw, Exception):
            imf_growth_series = _parse_imf(imf_growth_raw, "NGDP_RPCH")

        gdp_growth_combined = _merge_series(gdp_growth_series, imf_growth_series)

        # --- FDI series ---
        fdi_series: list[dict] = []
        if not isinstance(wb_fdi_raw, Exception):
            fdi_series = self.parse_world_bank(wb_fdi_raw, unit="% of GDP", source="World Bank")

        # --- Inflation series ---
        inflation_series: list[dict] = []
        if not isinstance(wb_inflation_raw, Exception):
            inflation_series = self.parse_world_bank(
                wb_inflation_raw, unit="%", source="World Bank"
            )

        imf_inflation_series: list[dict] = []
        if not isinstance(imf_inflation_raw, Exception):
            imf_inflation_series = _parse_imf(imf_inflation_raw, "PCPIPCH")

        inflation_combined = _merge_series(inflation_series, imf_inflation_series)

        # --- Additional indicators list ---
        indicators: list[dict] = []

        if not isinstance(wb_exports_raw, Exception):
            latest = self.latest_world_bank(wb_exports_raw, source="World Bank")
            if latest:
                indicators.append(
                    {
                        "name": "Exports of Goods & Services",
                        "value": round(latest["value"], 2),
                        "unit": "% of GDP",
                        "year": latest["year"],
                        "source": "World Bank",
                    }
                )

        if not isinstance(wb_manufacturing_raw, Exception):
            latest = self.latest_world_bank(wb_manufacturing_raw, source="World Bank")
            if latest:
                indicators.append(
                    {
                        "name": "Manufacturing Value Added",
                        "value": round(latest["value"], 2),
                        "unit": "% of GDP",
                        "year": latest["year"],
                        "source": "World Bank",
                    }
                )

        if not isinstance(wb_ease_raw, Exception):
            latest = self.latest_world_bank(wb_ease_raw, source="World Bank")
            if latest:
                indicators.append(
                    {
                        "name": "Ease of Doing Business Rank",
                        "value": round(latest["value"], 0),
                        "unit": "rank (lower = better)",
                        "year": latest["year"],
                        "source": "World Bank",
                    }
                )

        # --- News ---
        all_news: list[dict] = []
        if isinstance(gdelt_news, list):
            all_news.extend(gdelt_news)
        if isinstance(rss_news, list):
            all_news.extend(rss_news)

        # Optional: NewsAPI / GNews
        optional_news = await asyncio.gather(
            self._news_agent.fetch_newsapi("india economy GDP", max_items=5),
            self._news_agent.fetch_gnews("india economy", max_items=5),
            return_exceptions=True,
        )
        for res in optional_news:
            if isinstance(res, list):
                all_news.extend(res)

        # Deduplicate
        from .news_agent import _deduplicate_news
        all_news = _deduplicate_news(all_news)

        return {
            "gdp": gdp_entry,
            "gdpGrowth": gdp_growth_combined,
            "fdi": fdi_series,
            "inflation": inflation_combined,
            "indicators": indicators,
            "news": all_news[:20],
            "lastUpdated": _now_iso(),
        }


def _merge_series(primary: list[dict], secondary: list[dict]) -> list[dict]:
    """
    Merge two year-keyed series. Primary values take precedence.
    Secondary fills in years missing from primary.
    Result is sorted ascending by year.
    """
    year_map: dict[int, dict] = {entry["year"]: entry for entry in primary}
    for entry in secondary:
        if entry["year"] not in year_map:
            year_map[entry["year"]] = entry
    merged = list(year_map.values())
    merged.sort(key=lambda x: x["year"])
    return merged
