"""
Health Agent — global disease outbreak and vaccination coverage data.

Sources:
1. WHO Disease Outbreak News (RSS) — live outbreak alerts
2. CDC Traveler Health Notices (RSS) — travel health alerts
3. ReliefWeb Disasters API — epidemic/disease disasters
4. World Bank vaccination indicators:
   - SH.IMM.MEAS  (measles immunisation % of children)
   - SH.IMM.DPT   (DPT immunisation % of children)
5. Our World in Data COVID-19 latest CSV (GitHub)

Returns:
  {outbreaks, vaccinationData, summary}
"""
from __future__ import annotations


import asyncio
import csv
import io
import logging
from datetime import datetime, timezone

from .base_agent import BaseAgent, _strip_html

logger = logging.getLogger(__name__)

WHO_RSS_URL = "https://www.who.int/feeds/entity/csr/don/en/rss.xml"
CDC_RSS_URL = "https://wwwnc.cdc.gov/travel/rss/destinationUpdates.xml"
RELIEFWEB_URL = "https://api.reliefweb.int/v1/disasters"
WB_MEASLES_URL = (
    "https://api.worldbank.org/v2/country/all/indicator/SH.IMM.MEAS"
    "?format=json&per_page=300&mrv=1"
)
WB_DPT_URL = (
    "https://api.worldbank.org/v2/country/all/indicator/SH.IMM.DPT"
    "?format=json&per_page=300&mrv=1"
)
OWID_COVID_URL = (
    "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/latest/owid-covid-latest.csv"
)

# Known country centroids for outbreak geocoding (ISO-3166-1 alpha-2)
COUNTRY_COORDS: dict[str, tuple[float, float]] = {
    "AF": (33.93, 67.71), "AO": (-11.20, 17.87), "AR": (-38.42, -63.62),
    "BD": (23.68, 90.36), "BF": (12.36, -1.56), "BI": (-3.37, 29.92),
    "BR": (-14.24, -51.93), "CD": (-4.04, 21.76), "CF": (6.61, 20.94),
    "CG": (-0.23, 15.83), "CI": (7.54, -5.55), "CM": (3.85, 11.50),
    "CN": (35.86, 104.19), "CO": (4.57, -74.30), "DE": (51.17, 10.45),
    "EG": (26.82, 30.80), "ET": (9.15, 40.49), "FR": (46.23, 2.21),
    "GB": (55.38, -3.44), "GH": (7.95, -1.02), "GM": (13.44, -15.31),
    "GN": (9.95, -9.70), "GW": (11.80, -15.18), "HT": (18.97, -72.29),
    "ID": (-0.79, 113.92), "IN": (20.59, 78.96), "IQ": (33.22, 43.68),
    "IR": (32.43, 53.69), "IT": (41.87, 12.57), "JP": (36.20, 138.25),
    "KE": (-0.02, 37.91), "KH": (12.57, 104.99), "LB": (33.85, 35.86),
    "LR": (6.43, -9.43), "LY": (26.34, 17.23), "MA": (31.79, -7.09),
    "ML": (17.57, -3.99), "MM": (21.92, 95.96), "MR": (21.01, -10.94),
    "MW": (-13.25, 34.30), "MX": (23.63, -102.55), "MZ": (-18.67, 35.53),
    "NE": (17.61, 8.08), "NG": (9.08, 8.68), "PH": (12.88, 121.77),
    "PK": (30.38, 69.35), "RU": (61.52, 105.32), "RW": (-1.94, 29.87),
    "SD": (12.86, 30.22), "SL": (8.46, -11.78), "SN": (14.50, -14.45),
    "SO": (5.15, 46.20), "SS": (6.88, 31.57), "SY": (34.80, 38.99),
    "TD": (15.45, 18.73), "TG": (8.62, 0.82), "TZ": (-6.37, 34.89),
    "UA": (48.38, 31.17), "UG": (1.37, 32.29), "US": (37.09, -95.71),
    "VE": (6.42, -66.59), "YE": (15.55, 48.52), "ZA": (-30.56, 22.94),
    "ZM": (-13.13, 27.85), "ZW": (-19.02, 29.15),
}

# World Bank alpha-3 → alpha-2 mapping (subset)
WB_ISO3_TO_ISO2: dict[str, str] = {
    "AFG": "AF", "AGO": "AO", "ARG": "AR", "AUS": "AU", "AUT": "AT",
    "BDI": "BI", "BEN": "BJ", "BFA": "BF", "BGD": "BD", "BLR": "BY",
    "BOL": "BO", "BRA": "BR", "CAF": "CF", "CAN": "CA", "CHE": "CH",
    "CHL": "CL", "CHN": "CN", "CIV": "CI", "CMR": "CM", "COD": "CD",
    "COG": "CG", "COL": "CO", "DEU": "DE", "DJI": "DJ", "EGY": "EG",
    "ESP": "ES", "ETH": "ET", "FIN": "FI", "FRA": "FR", "GBR": "GB",
    "GHA": "GH", "GMB": "GM", "GNB": "GW", "GNQ": "GQ", "GTM": "GT",
    "GIN": "GN", "HTI": "HT", "IDN": "ID", "IND": "IN", "IRN": "IR",
    "IRQ": "IQ", "ITA": "IT", "JPN": "JP", "KEN": "KE", "KHM": "KH",
    "LBN": "LB", "LBR": "LR", "LBY": "LY", "MAR": "MA", "MDG": "MG",
    "MLI": "ML", "MMR": "MM", "MOZ": "MZ", "MRT": "MR", "MWI": "MW",
    "MEX": "MX", "NER": "NE", "NGA": "NG", "NLD": "NL", "NOR": "NO",
    "NPL": "NP", "PAK": "PK", "PHL": "PH", "POL": "PL", "PRK": "KP",
    "RUS": "RU", "RWA": "RW", "SAU": "SA", "SDN": "SD", "SEN": "SN",
    "SLE": "SL", "SOM": "SO", "SSD": "SS", "SWE": "SE", "SYR": "SY",
    "TCD": "TD", "TGO": "TG", "TZA": "TZ", "UGA": "UG", "UKR": "UA",
    "URY": "UY", "USA": "US", "VEN": "VE", "VNM": "VN", "YEM": "YE",
    "ZAF": "ZA", "ZMB": "ZM", "ZWE": "ZW",
}


def _severity_from_title(title: str) -> str:
    lower = title.lower()
    if any(k in lower for k in ("ebola", "plague", "cholera", "marburg", "yellow fever", "mpox", "monkeypox")):
        return "HIGH"
    if any(k in lower for k in ("outbreak", "epidemic", "surge", "alert")):
        return "MEDIUM"
    return "LOW"


class HealthAgent(BaseAgent):
    cache_prefix = "health"

    # ------------------------------------------------------------------
    # WHO outbreak RSS
    # ------------------------------------------------------------------
    async def _fetch_who_outbreaks(self) -> list[dict]:
        items = await self.fetch_rss(WHO_RSS_URL, source_name="WHO", max_items=30)
        outbreaks = []
        for idx, item in enumerate(items):
            title = item.get("title", "")
            outbreaks.append({
                "id": f"who-{idx}",
                "country": None,
                "lat": None,
                "lon": None,
                "disease": title,
                "status": "Active",
                "reportDate": item.get("publishedAt", ""),
                "severity": _severity_from_title(title),
                "url": item.get("url", ""),
                "description": item.get("summary", ""),
                "source": "WHO",
            })
        return outbreaks

    # ------------------------------------------------------------------
    # CDC travel health RSS
    # ------------------------------------------------------------------
    async def _fetch_cdc_outbreaks(self) -> list[dict]:
        items = await self.fetch_rss(CDC_RSS_URL, source_name="CDC", max_items=20)
        outbreaks = []
        for idx, item in enumerate(items):
            title = item.get("title", "")
            outbreaks.append({
                "id": f"cdc-{idx}",
                "country": None,
                "lat": None,
                "lon": None,
                "disease": title,
                "status": "Alert",
                "reportDate": item.get("publishedAt", ""),
                "severity": _severity_from_title(title),
                "url": item.get("url", ""),
                "description": item.get("summary", ""),
                "source": "CDC",
            })
        return outbreaks

    # ------------------------------------------------------------------
    # ReliefWeb epidemic disasters
    # ------------------------------------------------------------------
    async def _fetch_reliefweb_outbreaks(self) -> list[dict]:
        params = {
            "filter[field]": "type.name",
            "filter[value]": "Epidemic",
            "fields[include][]": ["name", "country", "date", "status", "url"],
            "limit": "30",
            "sort[]": "date.created:desc",
        }
        # ReliefWeb uses array params — build URL manually
        url = (
            "https://api.reliefweb.int/v1/disasters"
            "?filter[field]=type.name&filter[value]=Epidemic"
            "&fields[include][]=name&fields[include][]=country"
            "&fields[include][]=date&fields[include][]=status"
            "&fields[include][]=url&limit=30&sort[]=date.created:desc"
        )
        data = await self.fetch_json(url, cache_key=f"{self.cache_prefix}:reliefweb")
        outbreaks = []
        if not data or not isinstance(data, dict):
            return outbreaks
        for idx, item in enumerate(data.get("data", [])):
            fields = item.get("fields", {})
            name = fields.get("name", "")
            country_list = fields.get("country") or []
            country_name = country_list[0].get("name", "") if country_list else ""
            iso2 = (country_list[0].get("iso3", "") if country_list else "")
            iso2 = WB_ISO3_TO_ISO2.get(iso2.upper(), "")
            coords = COUNTRY_COORDS.get(iso2, (None, None))
            date_obj = (fields.get("date") or {}).get("created", "")
            status = fields.get("status", "alert")
            outbreaks.append({
                "id": f"rw-{item.get('id', idx)}",
                "country": country_name,
                "lat": coords[0],
                "lon": coords[1],
                "disease": name,
                "status": status.capitalize(),
                "reportDate": date_obj,
                "severity": _severity_from_title(name),
                "url": (fields.get("url") or {}).get("canonical", ""),
                "description": "",
                "source": "ReliefWeb",
            })
        return outbreaks

    # ------------------------------------------------------------------
    # World Bank vaccination rates
    # ------------------------------------------------------------------
    async def _fetch_vaccination(self) -> list[dict]:
        measles_raw, dpt_raw = await asyncio.gather(
            self.fetch_json(WB_MEASLES_URL, cache_key=f"{self.cache_prefix}:wb_measles"),
            self.fetch_json(WB_DPT_URL, cache_key=f"{self.cache_prefix}:wb_dpt"),
            return_exceptions=True,
        )

        measles_map: dict[str, float] = {}
        dpt_map: dict[str, float] = {}

        if isinstance(measles_raw, list) and len(measles_raw) > 1:
            for rec in (measles_raw[1] or []):
                if not isinstance(rec, dict) or rec.get("value") is None:
                    continue
                code = (rec.get("countryiso3code") or "").upper()
                iso2 = WB_ISO3_TO_ISO2.get(code, "")
                try:
                    measles_map[iso2 or code] = round(float(rec["value"]), 1)
                except (TypeError, ValueError):
                    pass

        if isinstance(dpt_raw, list) and len(dpt_raw) > 1:
            for rec in (dpt_raw[1] or []):
                if not isinstance(rec, dict) or rec.get("value") is None:
                    continue
                code = (rec.get("countryiso3code") or "").upper()
                iso2 = WB_ISO3_TO_ISO2.get(code, "")
                try:
                    dpt_map[iso2 or code] = round(float(rec["value"]), 1)
                except (TypeError, ValueError):
                    pass

        # Build combined records for countries that appear in measles data
        vax_data = []
        for code, measles_rate in measles_map.items():
            coords = COUNTRY_COORDS.get(code, (None, None))
            vax_data.append({
                "countryCode": code,
                "country": code,
                "lat": coords[0],
                "lon": coords[1],
                "measlesRate": measles_rate,
                "dptRate": dpt_map.get(code),
            })

        return vax_data

    # ------------------------------------------------------------------
    # Our World in Data COVID CSV (latest)
    # ------------------------------------------------------------------
    async def _fetch_owid_covid(self) -> list[dict]:
        text = await self.fetch_text(OWID_COVID_URL, cache_key=f"{self.cache_prefix}:owid_covid")
        if not text:
            return []
        records = []
        try:
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                iso_code = row.get("iso_code", "")
                # Skip aggregates (OWID_*)
                if iso_code.startswith("OWID_") or not iso_code:
                    continue
                location = row.get("location", "")
                total_cases = row.get("total_cases") or None
                total_deaths = row.get("total_deaths") or None
                new_cases = row.get("new_cases") or None
                date = row.get("date", "")
                try:
                    lat = float(row.get("latitude") or 0) or None
                    lon = float(row.get("longitude") or 0) or None
                except (TypeError, ValueError):
                    lat, lon = None, None
                records.append({
                    "isoCode": iso_code,
                    "country": location,
                    "lat": lat,
                    "lon": lon,
                    "totalCases": int(float(total_cases)) if total_cases else None,
                    "totalDeaths": int(float(total_deaths)) if total_deaths else None,
                    "newCases": int(float(new_cases)) if new_cases else None,
                    "date": date,
                })
        except Exception as exc:
            logger.warning("HealthAgent: OWID CSV parse error: %s", exc)
        return records

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    async def fetch_data(self) -> dict:
        cache_key = f"{self.cache_prefix}:all"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        who_task = self._fetch_who_outbreaks()
        cdc_task = self._fetch_cdc_outbreaks()
        rw_task = self._fetch_reliefweb_outbreaks()
        vax_task = self._fetch_vaccination()
        covid_task = self._fetch_owid_covid()

        results = await asyncio.gather(
            who_task, cdc_task, rw_task, vax_task, covid_task,
            return_exceptions=True,
        )

        who_outbreaks, cdc_outbreaks, rw_outbreaks, vax_data, covid_data = results

        all_outbreaks: list[dict] = []
        for batch in (who_outbreaks, cdc_outbreaks, rw_outbreaks):
            if isinstance(batch, list):
                all_outbreaks.extend(batch)

        vaccination_records: list[dict] = vax_data if isinstance(vax_data, list) else []
        covid_records: list[dict] = covid_data if isinstance(covid_data, list) else []

        critical = sum(1 for o in all_outbreaks if o.get("severity") == "HIGH")
        countries = len({o.get("country") for o in all_outbreaks if o.get("country")})

        result = {
            "outbreaks": all_outbreaks,
            "vaccinationData": vaccination_records,
            "covidData": covid_records,
            "summary": {
                "totalOutbreaks": len(all_outbreaks),
                "criticalOutbreaks": critical,
                "countries": countries,
            },
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

        self._cache[cache_key] = result
        return result
