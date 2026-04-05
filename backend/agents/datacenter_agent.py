"""
Datacenter Agent — global data center, cloud region, and internet exchange data.

Sources:
1. PeeringDB Facilities API (free, no key): https://www.peeringdb.com/api/fac
2. PeeringDB Internet Exchange API:         https://www.peeringdb.com/api/ix
3. Static cloud region catalogue (AWS, GCP, Azure, Alibaba, Oracle)
4. Static submarine cable landing points (well-known)

Returns:
  {datacenters, cloudRegions, internetExchanges, summary}
"""

import asyncio
import logging
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

PEERINGDB_FAC_URL = "https://www.peeringdb.com/api/fac"
PEERINGDB_IX_URL = "https://www.peeringdb.com/api/ix"

# ---------------------------------------------------------------------------
# Static cloud region data (publicly documented)
# ---------------------------------------------------------------------------
CLOUD_REGIONS: list[dict] = [
    # AWS
    {"provider": "AWS", "region": "us-east-1",      "name": "US East (N. Virginia)",    "lat": 38.13,  "lon": -78.45,  "services": ["compute", "storage", "database"]},
    {"provider": "AWS", "region": "us-east-2",      "name": "US East (Ohio)",            "lat": 40.41,  "lon": -83.00,  "services": ["compute", "storage"]},
    {"provider": "AWS", "region": "us-west-1",      "name": "US West (N. California)",   "lat": 37.77,  "lon": -122.41, "services": ["compute", "storage"]},
    {"provider": "AWS", "region": "us-west-2",      "name": "US West (Oregon)",          "lat": 45.52,  "lon": -122.67, "services": ["compute", "storage", "database"]},
    {"provider": "AWS", "region": "ca-central-1",   "name": "Canada (Central)",          "lat": 45.42,  "lon": -75.70,  "services": ["compute", "storage"]},
    {"provider": "AWS", "region": "eu-west-1",      "name": "Europe (Ireland)",          "lat": 53.33,  "lon": -6.25,   "services": ["compute", "storage", "database"]},
    {"provider": "AWS", "region": "eu-west-2",      "name": "Europe (London)",           "lat": 51.51,  "lon": -0.12,   "services": ["compute", "storage"]},
    {"provider": "AWS", "region": "eu-west-3",      "name": "Europe (Paris)",            "lat": 48.86,  "lon": 2.35,    "services": ["compute", "storage"]},
    {"provider": "AWS", "region": "eu-central-1",   "name": "Europe (Frankfurt)",        "lat": 50.11,  "lon": 8.68,    "services": ["compute", "storage", "database"]},
    {"provider": "AWS", "region": "eu-north-1",     "name": "Europe (Stockholm)",        "lat": 59.33,  "lon": 18.07,   "services": ["compute", "storage"]},
    {"provider": "AWS", "region": "eu-south-1",     "name": "Europe (Milan)",            "lat": 45.46,  "lon": 9.19,    "services": ["compute", "storage"]},
    {"provider": "AWS", "region": "ap-south-1",     "name": "Asia Pacific (Mumbai)",     "lat": 19.07,  "lon": 72.87,   "services": ["compute", "storage"]},
    {"provider": "AWS", "region": "ap-northeast-1", "name": "Asia Pacific (Tokyo)",      "lat": 35.68,  "lon": 139.69,  "services": ["compute", "storage", "database"]},
    {"provider": "AWS", "region": "ap-northeast-2", "name": "Asia Pacific (Seoul)",      "lat": 37.57,  "lon": 126.98,  "services": ["compute", "storage"]},
    {"provider": "AWS", "region": "ap-northeast-3", "name": "Asia Pacific (Osaka)",      "lat": 34.69,  "lon": 135.50,  "services": ["compute", "storage"]},
    {"provider": "AWS", "region": "ap-southeast-1", "name": "Asia Pacific (Singapore)",  "lat": 1.35,   "lon": 103.82,  "services": ["compute", "storage", "database"]},
    {"provider": "AWS", "region": "ap-southeast-2", "name": "Asia Pacific (Sydney)",     "lat": -33.86, "lon": 151.20,  "services": ["compute", "storage"]},
    {"provider": "AWS", "region": "ap-east-1",      "name": "Asia Pacific (Hong Kong)",  "lat": 22.39,  "lon": 114.10,  "services": ["compute", "storage"]},
    {"provider": "AWS", "region": "sa-east-1",      "name": "South America (São Paulo)", "lat": -23.54, "lon": -46.63,  "services": ["compute", "storage"]},
    {"provider": "AWS", "region": "me-south-1",     "name": "Middle East (Bahrain)",     "lat": 26.07,  "lon": 50.56,   "services": ["compute", "storage"]},
    {"provider": "AWS", "region": "af-south-1",     "name": "Africa (Cape Town)",        "lat": -33.92, "lon": 18.42,   "services": ["compute", "storage"]},
    # GCP
    {"provider": "GCP", "region": "us-central1",       "name": "Iowa",             "lat": 41.86,  "lon": -93.10,  "services": ["compute", "storage", "ml"]},
    {"provider": "GCP", "region": "us-east1",           "name": "South Carolina",   "lat": 33.83,  "lon": -81.16,  "services": ["compute", "storage"]},
    {"provider": "GCP", "region": "us-east4",           "name": "Northern Virginia","lat": 38.95,  "lon": -77.33,  "services": ["compute", "storage"]},
    {"provider": "GCP", "region": "us-west1",           "name": "Oregon",           "lat": 45.60,  "lon": -121.18, "services": ["compute", "storage"]},
    {"provider": "GCP", "region": "us-west2",           "name": "Los Angeles",      "lat": 34.05,  "lon": -118.24, "services": ["compute", "storage"]},
    {"provider": "GCP", "region": "europe-west1",       "name": "Belgium",          "lat": 50.45,  "lon": 3.82,    "services": ["compute", "storage"]},
    {"provider": "GCP", "region": "europe-west2",       "name": "London",           "lat": 51.51,  "lon": -0.12,   "services": ["compute", "storage"]},
    {"provider": "GCP", "region": "europe-west3",       "name": "Frankfurt",        "lat": 50.11,  "lon": 8.68,    "services": ["compute", "storage"]},
    {"provider": "GCP", "region": "europe-west4",       "name": "Netherlands",      "lat": 53.44,  "lon": 6.84,    "services": ["compute", "storage"]},
    {"provider": "GCP", "region": "europe-north1",      "name": "Finland",          "lat": 60.57,  "lon": 27.19,   "services": ["compute", "storage"]},
    {"provider": "GCP", "region": "asia-east1",         "name": "Taiwan",           "lat": 24.05,  "lon": 120.52,  "services": ["compute", "storage"]},
    {"provider": "GCP", "region": "asia-east2",         "name": "Hong Kong",        "lat": 22.39,  "lon": 114.10,  "services": ["compute", "storage"]},
    {"provider": "GCP", "region": "asia-northeast1",    "name": "Tokyo",            "lat": 35.68,  "lon": 139.69,  "services": ["compute", "storage", "ml"]},
    {"provider": "GCP", "region": "asia-southeast1",    "name": "Singapore",        "lat": 1.35,   "lon": 103.82,  "services": ["compute", "storage"]},
    {"provider": "GCP", "region": "asia-south1",        "name": "Mumbai",           "lat": 19.07,  "lon": 72.87,   "services": ["compute", "storage"]},
    {"provider": "GCP", "region": "australia-southeast1","name": "Sydney",          "lat": -33.86, "lon": 151.20,  "services": ["compute", "storage"]},
    {"provider": "GCP", "region": "southamerica-east1", "name": "São Paulo",        "lat": -23.54, "lon": -46.63,  "services": ["compute", "storage"]},
    # Azure
    {"provider": "Azure", "region": "eastus",           "name": "East US (Virginia)",      "lat": 37.36,  "lon": -79.38,  "services": ["compute", "storage", "database"]},
    {"provider": "Azure", "region": "eastus2",          "name": "East US 2",               "lat": 36.67,  "lon": -78.37,  "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "westus",           "name": "West US (California)",    "lat": 37.78,  "lon": -122.39, "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "westus2",          "name": "West US 2 (Washington)",  "lat": 47.23,  "lon": -119.85, "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "centralus",        "name": "Central US (Iowa)",       "lat": 41.59,  "lon": -93.62,  "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "northcentralus",   "name": "North Central US",        "lat": 41.85,  "lon": -87.65,  "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "southcentralus",   "name": "South Central US",        "lat": 29.42,  "lon": -98.49,  "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "canadacentral",    "name": "Canada Central",          "lat": 43.65,  "lon": -79.38,  "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "northeurope",      "name": "North Europe (Ireland)",  "lat": 53.33,  "lon": -6.25,   "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "westeurope",       "name": "West Europe (Netherlands)","lat": 52.37, "lon": 4.89,    "services": ["compute", "storage", "database"]},
    {"provider": "Azure", "region": "uksouth",          "name": "UK South",                "lat": 51.51,  "lon": -0.12,   "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "germanywestcentral","name": "Germany West Central",   "lat": 50.11,  "lon": 8.68,    "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "francecentral",    "name": "France Central",          "lat": 46.30,  "lon": 2.21,    "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "switzerlandnorth", "name": "Switzerland North",       "lat": 47.45,  "lon": 8.56,    "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "eastasia",         "name": "East Asia (Hong Kong)",   "lat": 22.39,  "lon": 114.10,  "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "southeastasia",    "name": "Southeast Asia (Singapore)","lat": 1.35, "lon": 103.82,  "services": ["compute", "storage", "database"]},
    {"provider": "Azure", "region": "japaneast",        "name": "Japan East",              "lat": 35.68,  "lon": 139.69,  "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "koreacentral",     "name": "Korea Central",           "lat": 37.57,  "lon": 126.98,  "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "centralindia",     "name": "Central India",           "lat": 18.52,  "lon": 73.86,   "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "australiaeast",    "name": "Australia East",          "lat": -33.86, "lon": 151.20,  "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "brazilsouth",      "name": "Brazil South",            "lat": -23.54, "lon": -46.63,  "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "uaenorth",         "name": "UAE North",               "lat": 25.27,  "lon": 55.30,   "services": ["compute", "storage"]},
    {"provider": "Azure", "region": "southafricanorth", "name": "South Africa North",      "lat": -25.73, "lon": 28.22,   "services": ["compute", "storage"]},
    # Alibaba Cloud
    {"provider": "Alibaba", "region": "cn-hangzhou",    "name": "China (Hangzhou)",    "lat": 30.27,  "lon": 120.15, "services": ["compute", "storage"]},
    {"provider": "Alibaba", "region": "cn-beijing",     "name": "China (Beijing)",     "lat": 39.90,  "lon": 116.40, "services": ["compute", "storage"]},
    {"provider": "Alibaba", "region": "cn-shanghai",    "name": "China (Shanghai)",    "lat": 31.23,  "lon": 121.47, "services": ["compute", "storage"]},
    {"provider": "Alibaba", "region": "ap-southeast-1", "name": "Asia Pacific (Singapore)", "lat": 1.35, "lon": 103.82, "services": ["compute", "storage"]},
    {"provider": "Alibaba", "region": "ap-northeast-1", "name": "Asia Pacific (Japan)","lat": 35.68,  "lon": 139.69, "services": ["compute", "storage"]},
    {"provider": "Alibaba", "region": "eu-central-1",   "name": "Europe (Germany)",    "lat": 50.11,  "lon": 8.68,   "services": ["compute", "storage"]},
    {"provider": "Alibaba", "region": "us-east-1",      "name": "US East (Virginia)",  "lat": 38.13,  "lon": -78.45, "services": ["compute", "storage"]},
    # Oracle Cloud
    {"provider": "Oracle", "region": "us-phoenix-1",    "name": "US West (Phoenix)",   "lat": 33.45,  "lon": -112.07, "services": ["compute", "storage"]},
    {"provider": "Oracle", "region": "us-ashburn-1",    "name": "US East (Ashburn)",   "lat": 39.04,  "lon": -77.49,  "services": ["compute", "storage"]},
    {"provider": "Oracle", "region": "eu-frankfurt-1",  "name": "Germany Central",     "lat": 50.11,  "lon": 8.68,    "services": ["compute", "storage"]},
    {"provider": "Oracle", "region": "uk-london-1",     "name": "UK South (London)",   "lat": 51.51,  "lon": -0.12,   "services": ["compute", "storage"]},
    {"provider": "Oracle", "region": "ap-tokyo-1",      "name": "Japan East (Tokyo)",  "lat": 35.68,  "lon": 139.69,  "services": ["compute", "storage"]},
    {"provider": "Oracle", "region": "ap-sydney-1",     "name": "Australia East",      "lat": -33.86, "lon": 151.20,  "services": ["compute", "storage"]},
    {"provider": "Oracle", "region": "sa-saopaulo-1",   "name": "Brazil East",         "lat": -23.54, "lon": -46.63,  "services": ["compute", "storage"]},
]


class DatacenterAgent(BaseAgent):
    cache_prefix = "datacenters"

    # ------------------------------------------------------------------
    # PeeringDB Facilities
    # ------------------------------------------------------------------
    async def _fetch_peeringdb_facilities(self) -> list[dict]:
        params = {"limit": "500", "offset": "0", "status": "ok"}
        data = await self.fetch_json(
            PEERINGDB_FAC_URL,
            params=params,
            cache_key=f"{self.cache_prefix}:peeringdb_fac",
        )
        if not data or not isinstance(data, dict):
            return []

        facilities = []
        for item in (data.get("data") or []):
            if not isinstance(item, dict):
                continue
            lat = item.get("latitude")
            lon = item.get("longitude")
            if lat is None or lon is None:
                continue
            try:
                lat, lon = float(lat), float(lon)
            except (TypeError, ValueError):
                continue

            org_name = item.get("org_name") or item.get("name") or "Unknown"
            city = item.get("city", "")
            country = item.get("country", "")

            facilities.append({
                "id": f"pdb-fac-{item.get('id', '')}",
                "name": item.get("name", org_name),
                "lat": round(lat, 5),
                "lon": round(lon, 5),
                "city": city,
                "country": country,
                "provider": org_name,
                "type": "datacenter",
                "tier": None,
                "website": item.get("website", ""),
            })
        return facilities

    # ------------------------------------------------------------------
    # PeeringDB Internet Exchanges
    # ------------------------------------------------------------------
    async def _fetch_peeringdb_ix(self) -> list[dict]:
        params = {"limit": "500", "offset": "0", "status": "ok"}
        data = await self.fetch_json(
            PEERINGDB_IX_URL,
            params=params,
            cache_key=f"{self.cache_prefix}:peeringdb_ix",
        )
        if not data or not isinstance(data, dict):
            return []

        exchanges = []
        for item in (data.get("data") or []):
            if not isinstance(item, dict):
                continue
            city = item.get("city", "")
            country = item.get("country", "")
            name = item.get("name", "")
            # PeeringDB IX doesn't carry lat/lon directly; skip those without
            lat = item.get("latitude")
            lon = item.get("longitude")
            if lat is None or lon is None:
                continue
            try:
                lat, lon = float(lat), float(lon)
            except (TypeError, ValueError):
                continue

            speed = item.get("media", "")
            exchanges.append({
                "id": f"pdb-ix-{item.get('id', '')}",
                "name": name,
                "lat": round(lat, 5),
                "lon": round(lon, 5),
                "city": city,
                "country": country,
                "speed": speed,
                "website": item.get("website", ""),
            })
        return exchanges

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    async def fetch_data(self) -> dict:
        cache_key = f"{self.cache_prefix}:all"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        fac_task = self._fetch_peeringdb_facilities()
        ix_task = self._fetch_peeringdb_ix()

        fac_result, ix_result = await asyncio.gather(
            fac_task, ix_task, return_exceptions=True,
        )

        datacenters: list[dict] = fac_result if isinstance(fac_result, list) else []
        internet_exchanges: list[dict] = ix_result if isinstance(ix_result, list) else []

        # Compute summary
        countries_dc = len({d.get("country") for d in datacenters if d.get("country")})
        countries_ix = len({ix.get("country") for ix in internet_exchanges if ix.get("country")})

        result = {
            "datacenters": datacenters,
            "cloudRegions": CLOUD_REGIONS,
            "internetExchanges": internet_exchanges,
            "summary": {
                "totalDatacenters": len(datacenters),
                "totalCloudRegions": len(CLOUD_REGIONS),
                "totalIX": len(internet_exchanges),
                "countries": max(countries_dc, countries_ix),
            },
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

        self._cache[cache_key] = result
        return result
