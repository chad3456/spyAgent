"""
DDoS Agent — real-time DDoS and cyber-attack data.

Source priority:
1. Cloudflare Radar API (Layer 3 + Layer 7 attack origins, requires CF_RADAR_TOKEN)
2. GDELT cybersecurity/DDoS news to synthesize country risk scores when CF is unavailable

Returns country-level attack data:
  {country, countryCode, lat, lon, attackCount, severity, bandwidth}
"""
from __future__ import annotations


import asyncio
import logging
import os
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

CF_RADAR_BASE = "https://api.cloudflare.com/client/v4/radar"

# Approximate country centroids for mapping (ISO-3166-1 alpha-2 → [lat, lon])
COUNTRY_COORDS: dict[str, tuple[float, float]] = {
    "US": (37.09, -95.71),
    "CN": (35.86, 104.19),
    "RU": (61.52, 105.32),
    "DE": (51.17, 10.45),
    "GB": (55.38, -3.44),
    "FR": (46.23, 2.21),
    "IN": (20.59, 78.96),
    "BR": (-14.24, -51.93),
    "JP": (36.20, 138.25),
    "KR": (35.91, 127.77),
    "NL": (52.13, 5.29),
    "UA": (48.38, 31.17),
    "CA": (56.13, -106.35),
    "AU": (-25.27, 133.78),
    "SG": (1.35, 103.82),
    "HK": (22.40, 114.11),
    "TR": (38.96, 35.24),
    "VN": (14.06, 108.28),
    "ID": (-0.79, 113.92),
    "IR": (32.43, 53.69),
    "TH": (15.87, 100.99),
    "NG": (9.08, 8.68),
    "MX": (23.63, -102.55),
    "PL": (51.92, 19.15),
    "ZA": (-30.56, 22.94),
    "IT": (41.87, 12.57),
    "ES": (40.46, -3.75),
    "SE": (60.13, 18.64),
    "NO": (60.47, 8.47),
    "FI": (61.92, 25.75),
    "PK": (30.38, 69.35),
    "BD": (23.68, 90.36),
    "MY": (4.21, 101.97),
    "PH": (12.88, 121.77),
    "EG": (26.82, 30.80),
    "IL": (31.05, 34.85),
    "SA": (23.89, 45.08),
    "AR": (-38.42, -63.62),
    "CL": (-35.68, -71.54),
    "CO": (4.57, -74.30),
}

# Severity thresholds based on normalised attack count
def _severity(count: float, max_count: float) -> str:
    if max_count <= 0:
        return "LOW"
    ratio = count / max_count
    if ratio >= 0.75:
        return "CRITICAL"
    if ratio >= 0.50:
        return "HIGH"
    if ratio >= 0.25:
        return "MEDIUM"
    return "LOW"


class DDoSAgent(BaseAgent):
    cache_prefix = "ddos"

    def __init__(self, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self._cf_token = os.getenv("CF_RADAR_TOKEN", "").strip() or None

    # ------------------------------------------------------------------
    # Cloudflare Radar — Layer 3 (volumetric) attack origins
    # ------------------------------------------------------------------
    async def _fetch_cf_layer3(self) -> list[dict]:
        if not self._cf_token:
            return []
        url = f"{CF_RADAR_BASE}/attacks/layer3/top/locations/origin"
        headers_extra = {"Authorization": f"Bearer {self._cf_token}"}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    params={"limit": "50", "format": "json"},
                    headers={"Authorization": f"Bearer {self._cf_token}", "Accept": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.warning("CF Radar L3 failed: %s", exc)
            return []

        if not data or not data.get("success"):
            return []

        rows = (data.get("result", {}) or {}).get("top_0", [])
        return self._parse_cf_rows(rows, source="cloudflare_l3")

    # ------------------------------------------------------------------
    # Cloudflare Radar — Layer 7 (application) attack origins
    # ------------------------------------------------------------------
    async def _fetch_cf_layer7(self) -> list[dict]:
        if not self._cf_token:
            return []
        url = f"{CF_RADAR_BASE}/attacks/layer7/top/locations/origin"
        try:
            import httpx
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    params={"limit": "50", "format": "json"},
                    headers={"Authorization": f"Bearer {self._cf_token}", "Accept": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.warning("CF Radar L7 failed: %s", exc)
            return []

        if not data or not data.get("success"):
            return []

        rows = (data.get("result", {}) or {}).get("top_0", [])
        return self._parse_cf_rows(rows, source="cloudflare_l7")

    @staticmethod
    def _parse_cf_rows(rows: list, source: str) -> list[dict]:
        results = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            code = (row.get("clientCountryAlpha2") or row.get("location") or "").upper().strip()
            name = row.get("clientCountryName") or row.get("locationName") or code
            value = row.get("value") or row.get("rank") or 0
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = 0.0
            coords = COUNTRY_COORDS.get(code, (0.0, 0.0))
            if code:
                results.append({
                    "countryCode": code,
                    "country": name,
                    "lat": coords[0],
                    "lon": coords[1],
                    "attackCount": value,
                    "bandwidth": None,
                    "source": source,
                })
        return results

    # ------------------------------------------------------------------
    # GDELT fallback — synthesise risk scores from news volume
    # ------------------------------------------------------------------
    async def _fetch_gdelt_fallback(self) -> list[dict]:
        queries = [
            "DDoS attack cyber",
            "cyberattack hacker botnet",
            "ransomware cyber warfare",
        ]
        tasks = [
            self.fetch_gdelt(q, max_records=25, category="cyber")
            for q in queries
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        country_counts: dict[str, int] = {}
        country_names: dict[str, str] = {}

        for batch in results:
            if isinstance(batch, Exception):
                continue
            for art in batch:
                # GDELT articles carry a sourcecountry field (2-letter)
                country_code = (art.get("source") or "")[:2].upper()
                if len(country_code) == 2 and country_code.isalpha():
                    country_counts[country_code] = country_counts.get(country_code, 0) + 1

        records = []
        for code, count in country_counts.items():
            coords = COUNTRY_COORDS.get(code, (0.0, 0.0))
            records.append({
                "countryCode": code,
                "country": country_names.get(code, code),
                "lat": coords[0],
                "lon": coords[1],
                "attackCount": float(count),
                "bandwidth": None,
                "source": "gdelt_inferred",
            })
        return records

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    async def fetch_data(self) -> dict:
        cache_key = f"{self.cache_prefix}:all"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        # Try CF Radar concurrently; fall back to GDELT if nothing returned
        l3_data, l7_data = await asyncio.gather(
            self._fetch_cf_layer3(),
            self._fetch_cf_layer7(),
            return_exceptions=False,
        )

        # Merge L3 + L7 by country code, summing attack counts
        merged: dict[str, dict] = {}
        for record in (l3_data + l7_data):
            code = record["countryCode"]
            if code in merged:
                merged[code]["attackCount"] = merged[code]["attackCount"] + record["attackCount"]
            else:
                merged[code] = dict(record)

        countries = list(merged.values())

        if not countries:
            logger.info("DDoSAgent: CF Radar unavailable, using GDELT fallback")
            countries = await self._fetch_gdelt_fallback()

        # Compute severity relative to max
        if countries:
            max_count = max(c["attackCount"] for c in countries) or 1.0
            for c in countries:
                c["severity"] = _severity(c["attackCount"], max_count)
        else:
            max_count = 1.0

        # Sort descending by attack count
        countries.sort(key=lambda x: x["attackCount"], reverse=True)

        result = {
            "countries": countries,
            "total": len(countries),
            "source": "cloudflare_radar" if (l3_data or l7_data) else "gdelt_inferred",
            "hasCFToken": self._cf_token is not None,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

        self._cache[cache_key] = result
        return result
