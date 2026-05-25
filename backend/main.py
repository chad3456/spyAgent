"""
OSINT Intelligence Platform - FastAPI Backend
=============================================

Multi-agent system that aggregates real-time global intelligence data from:
  - GDELT Document API V2 (free, no key)
  - OCHA HAPI Conflict Events (free, no key)
  - ACLED API (optional: ACLED_API_KEY + ACLED_EMAIL env vars)
  - OpenSky Network — live aircraft positions (free, no key)
  - ADS-B data — military aircraft detection (free)
  - USGS Earthquake Hazards Program (free, no key)
  - Cloudflare Radar API — DDoS attacks (optional: CF_RADAR_TOKEN)
  - Celestrak TLE + sgp4 — satellite positions (free, no key)
  - WHO RSS + World Bank — health alerts & vaccination (free)
  - PeeringDB + static cloud regions — datacenter infrastructure (free)
  - Twitter/X API v2 — verified geopolitical feeds (optional: TWITTER_BEARER_TOKEN)
  - NewsAPI + RSS feeds — intelligence news (optional: NEWS_API_KEY)
  - YouTube embed search + GDELT image gallery (streams)

Run locally:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Deploy to Render.com — see /render.yaml in repo root.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Import agents
# ---------------------------------------------------------------------------
from agents import (
    EconomicAgent, AIInfraAgent, InfrastructureAgent, DefenseAgent, NewsAgent,
    ProtestAgent, HAPIAgent, StreamAgent,
    FlightAgent, MilitaryFlightAgent, VesselAgent, EarthquakeAgent, DDoSAgent,
    SatelliteAgent, HealthAgent, DatacenterAgent, SocialMediaAgent, NewsIntelAgent,
    # Dhurandhar extended agents
    FiresAgent, InternetOutageAgent, SubmarineAgent, DroneAgent, CCTVAgent, SalvoAgent,
)

# Claude analyst team — synthesises the raw swarm output into intelligence products.
from agents.claude import (
    TeamCoordinator, ThreatAnalyst, CorrelationAgent, BriefingAgent,
    RegionalAnalyst, claude_available,
)
from agents.claude.regional_analyst import COUNTRY_PROFILES

# Local intel team — rule-based heuristics + optional Ollama polish. Works
# fully offline with no API key, producing the same response shape as the
# Claude team so the dashboard panel is engine-agnostic.
from agents.local_intel import LocalTeamCoordinator, ollama_available

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="OSINT Intelligence Platform API",
    description=(
        "Multi-domain real-time intelligence API: civil unrest, live flights, "
        "vessel tracking, earthquakes, DDoS attacks, satellites, health alerts, "
        "datacenter infrastructure, social feeds, and news intelligence."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — controlled via ALLOWED_ORIGINS env var.
# Default "*" works for development and initial deploys.
# In production set: ALLOWED_ORIGINS=https://your-site.netlify.app
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "*").strip()
_allow_origins: list[str] = (
    ["*"] if _raw_origins == "*" else [o.strip() for o in _raw_origins.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=_raw_origins != "*",
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Agent singletons (shared cache)
# ---------------------------------------------------------------------------
_timeout = float(os.environ.get("REQUEST_TIMEOUT", "30"))

# Existing agents
_economic_agent = EconomicAgent(timeout=_timeout)
_ai_infra_agent = AIInfraAgent(timeout=_timeout)
_infrastructure_agent = InfrastructureAgent(timeout=_timeout)
_defense_agent = DefenseAgent(timeout=_timeout)
_news_agent = NewsAgent(timeout=_timeout)
_protest_agent = ProtestAgent(timeout=_timeout)
_hapi_agent = HAPIAgent(timeout=_timeout)
_stream_agent = StreamAgent(timeout=_timeout)

# New OSINT intelligence agents
_flight_agent = FlightAgent(timeout=_timeout)
_military_flight_agent = MilitaryFlightAgent(timeout=_timeout)
_vessel_agent = VesselAgent(timeout=_timeout)
_earthquake_agent = EarthquakeAgent(timeout=_timeout)
_ddos_agent = DDoSAgent(timeout=_timeout)
_satellite_agent = SatelliteAgent(timeout=_timeout)
_health_agent = HealthAgent(timeout=_timeout)
_datacenter_agent = DatacenterAgent(timeout=_timeout)
_social_media_agent = SocialMediaAgent(timeout=_timeout)
_news_intel_agent = NewsIntelAgent(timeout=_timeout)

# Dhurandhar extended agents
_fires_agent = FiresAgent(timeout=_timeout)
_internet_outage_agent = InternetOutageAgent(timeout=_timeout)
_submarine_agent = SubmarineAgent(timeout=_timeout)
_drone_agent = DroneAgent(timeout=_timeout)
_cctv_agent = CCTVAgent(timeout=_timeout)
_salvo_agent = SalvoAgent(timeout=_timeout)

# Claude analyst team — built once, reused across requests.
_claude_team = TeamCoordinator()

# Local heuristic intel team — always available, no API key required.
_local_team = LocalTeamCoordinator()


def _active_team():
    """
    Pick the analyst team to use. Claude if its key is set; otherwise the
    local heuristic team. Override with ?engine=local or ?engine=claude on
    individual routes.
    """
    return _claude_team if claude_available() else _local_team


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["meta"])
async def health_check():
    """
    Liveness / readiness probe.
    Returns current UTC timestamp and service status.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "India Progress Dashboard API",
        "version": "1.0.0",
    }


@app.get("/api/economic", tags=["data"])
async def get_economic_data():
    """
    Macroeconomic indicators for India.

    Sources: World Bank, IMF DataMapper, GDELT, Economic Times RSS,
    Business Standard RSS. Optional: NewsAPI, GNews.

    Returns GDP, GDP growth series, FDI, inflation, exports, manufacturing,
    ease-of-doing-business, plus recent news articles.
    """
    try:
        data = await _economic_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("Economic agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch economic data: {exc}")


@app.get("/api/ai-infra", tags=["data"])
async def get_ai_infra_data():
    """
    India AI & technology infrastructure data.

    Sources: GDELT (AI/data-center/startup news), Economic Times RSS,
    PIB RSS. Optional: NewsAPI, GNews.

    Returns categorised news articles covering AI investments, data centres,
    startups, and technology policy.
    """
    try:
        data = await _ai_infra_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("AI Infra agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch AI/infra data: {exc}")


@app.get("/api/infrastructure", tags=["data"])
async def get_infrastructure_data():
    """
    India physical infrastructure data.

    Sources: World Bank (electricity, renewable energy), GDELT (roads,
    highways, power, solar news), PIB RSS.

    Returns time-series for power consumption and renewable energy share,
    plus recent infrastructure news.
    """
    try:
        data = await _infrastructure_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("Infrastructure agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch infrastructure data: {exc}")


@app.get("/api/defense", tags=["data"])
async def get_defense_data():
    """
    India defense and military expenditure data.

    Sources: World Bank (military expenditure % GDP and USD), GDELT
    (defense/military/weapons news), PIB RSS.

    Returns military spending time-series and recent defense news.
    """
    try:
        data = await _defense_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("Defense agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch defense data: {exc}")


@app.get("/api/summary", tags=["data"])
async def get_summary():
    """
    Aggregated summary: all domain data fetched concurrently.

    Runs all five agents in parallel and returns a combined payload
    with economic, AI/infrastructure, infrastructure, defense, and
    news data — plus a top-level news feed.

    This is the most comprehensive (and most expensive) endpoint;
    responses are cached for 15 minutes.
    """
    try:
        economic, ai_infra, infrastructure, defense, news = await asyncio.gather(
            _economic_agent.fetch_data(),
            _ai_infra_agent.fetch_data(),
            _infrastructure_agent.fetch_data(),
            _defense_agent.fetch_data(),
            _news_agent.fetch_data(),
            return_exceptions=True,
        )

        def _safe(result, label: str):
            if isinstance(result, Exception):
                logger.error("%s failed in summary: %s", label, result, exc_info=False)
                return {"error": str(result)}
            return result

        return {
            "economic": _safe(economic, "EconomicAgent"),
            "aiInfra": _safe(ai_infra, "AIInfraAgent"),
            "infrastructure": _safe(infrastructure, "InfrastructureAgent"),
            "defense": _safe(defense, "DefenseAgent"),
            "news": _safe(news, "NewsAgent"),
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.error("Summary endpoint error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch summary data: {exc}")


# ---------------------------------------------------------------------------
# Protest Map Routes
# ---------------------------------------------------------------------------

@app.get("/api/protests", tags=["protest-map"])
async def get_protests():
    """
    Global protest and demonstration events.

    Sources: GDELT Doc API V2 (always), ACLED (when ACLED_API_KEY + ACLED_EMAIL env vars set).

    Returns geolocated protest events with threat level assessments.
    """
    try:
        data = await _protest_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("Protest agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch protest data: {exc}")


@app.get("/api/hapi-events", tags=["protest-map"])
async def get_hapi_events():
    """
    Humanitarian conflict/protest events from OCHA HAPI.

    Source: OCHA Humanitarian API (hapi.humdata.org) — Protests and
    Demonstrations event types.

    Returns geolocated conflict events with threat level and fatality data.
    """
    try:
        data = await _hapi_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("HAPI agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch HAPI data: {exc}")


@app.get("/api/streams", tags=["protest-map"])
async def get_streams():
    """
    Live video stream embed URLs and protest imagery.

    Sources: YouTube embed search (no key required) and GDELT image gallery.

    Returns YouTube search embed links for live protest coverage plus
    recent protest images from GDELT.
    """
    try:
        data = await _stream_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("Stream agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch stream data: {exc}")


@app.get("/api/protest-map", tags=["protest-map"])
async def get_protest_map(demo: bool = False):
    """
    Aggregated protest map payload: all three protest data sources fetched concurrently.

    Add ?demo=true to skip live API calls and return rich seed data instantly
    (useful for previews, screenshots, and testing without API keys).
    """
    if demo:
        from demo_data import get_demo_protests, get_demo_hapi, get_demo_streams
        return {
            "protests": get_demo_protests(),
            "hapiEvents": get_demo_hapi(),
            "streams": get_demo_streams(),
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
            "isDemo": True,
        }

    try:
        protests, hapi_events, streams = await asyncio.gather(
            _protest_agent.fetch_data(),
            _hapi_agent.fetch_data(),
            _stream_agent.fetch_data(),
            return_exceptions=True,
        )

        def _safe(result, label: str):
            if isinstance(result, Exception):
                logger.error("%s failed in protest-map: %s", label, result, exc_info=False)
                return {"error": str(result)}
            return result

        return {
            "protests": _safe(protests, "ProtestAgent"),
            "hapiEvents": _safe(hapi_events, "HAPIAgent"),
            "streams": _safe(streams, "StreamAgent"),
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.error("Protest-map endpoint error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch protest map data: {exc}")


# ---------------------------------------------------------------------------
# OSINT Intelligence Routes
# ---------------------------------------------------------------------------

@app.get("/api/flights", tags=["osint"])
async def get_flights():
    """
    Live civil aircraft positions from OpenSky Network.
    Free API, no key required. Returns up to 500 airborne aircraft.
    """
    try:
        data = await _flight_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("Flight agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch flight data: {exc}")


@app.get("/api/flights/test", tags=["osint"])
async def test_flights():
    """
    Diagnostic endpoint: tests all three ADS-B sources and returns their status.
    Hit this first to verify your environment can reach live flight APIs.
    GET /api/flights/test
    """
    import httpx as _httpx

    async def _probe(url: str, name: str) -> dict:
        try:
            async with _httpx.AsyncClient(timeout=8.0, follow_redirects=True) as c:
                r = await c.get(url)
                if r.status_code == 200:
                    body = r.json()
                    count = len(
                        body.get("states") or body.get("ac") or body.get("aircraft") or []
                    )
                    return {"source": name, "status": "ok", "http": 200, "count": count}
                return {"source": name, "status": "error", "http": r.status_code, "count": 0}
        except Exception as e:
            return {"source": name, "status": "unreachable", "http": 0, "error": str(e)[:120], "count": 0}

    results = await asyncio.gather(
        _probe("https://opensky-network.org/api/states/all", "opensky"),
        _probe("https://api.adsb.lol/v2/aircraft", "adsb.lol"),
        _probe("https://api.airplanes.live/v2/aircraft", "airplanes.live"),
    )
    reachable = [r for r in results if r["status"] == "ok"]
    return {
        "sources": results,
        "reachable": len(reachable),
        "recommendation": reachable[0]["source"] if reachable else "none — check outbound network access",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/military-flights", tags=["osint"])
async def get_military_flights():
    """
    Military aircraft positions detected via ADS-B / OpenSky callsign filtering.
    Identifies aircraft with military callsign prefixes and ICAO hex ranges.
    """
    try:
        data = await _military_flight_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("Military flight agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch military flight data: {exc}")


@app.get("/api/vessels", tags=["osint"])
async def get_vessels():
    """
    Ship and vessel positions from AIS data sources.
    Includes commercial, military, and cargo vessels.
    """
    try:
        data = await _vessel_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("Vessel agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch vessel data: {exc}")


@app.get("/api/earthquakes", tags=["osint"])
async def get_earthquakes():
    """
    Real-time earthquake data from USGS Earthquake Hazards Program.
    Returns M2.5+ earthquakes from the past 7 days with severity classification.
    """
    try:
        data = await _earthquake_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("Earthquake agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch earthquake data: {exc}")


@app.get("/api/ddos", tags=["osint"])
async def get_ddos():
    """
    DDoS attack data by country with severity classification.
    Sources: Cloudflare Radar API (set CF_RADAR_TOKEN env var) with GDELT fallback.
    Bubble visualization data for country-level attack intensity.
    """
    try:
        data = await _ddos_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("DDoS agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch DDoS data: {exc}")


@app.get("/api/satellites", tags=["osint"])
async def get_satellites():
    """
    Live satellite positions computed from Celestrak TLE data using sgp4 propagation.
    Returns positions for ISS, weather, navigation, and Earth observation satellites.
    """
    try:
        data = await _satellite_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("Satellite agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch satellite data: {exc}")


@app.get("/api/satellites/test", tags=["osint"])
async def test_satellites():
    """
    Diagnostic endpoint: tests N2YO and Celestrak connectivity for satellite TLE data.
    Returns which TLE sources are reachable and whether N2YO_API_KEY is configured.
    GET /api/satellites/test
    """
    import httpx as _httpx

    n2yo_key = os.environ.get("N2YO_API_KEY", "").strip()

    async def _probe_celestrak(url: str, name: str) -> dict:
        try:
            async with _httpx.AsyncClient(timeout=8.0, follow_redirects=True) as c:
                r = await c.get(url)
                if r.status_code == 200:
                    lines = [l for l in r.text.splitlines() if l.strip()]
                    return {"source": name, "status": "ok", "http": 200, "tle_entries": len(lines) // 3}
                return {"source": name, "status": "error", "http": r.status_code}
        except Exception as e:
            return {"source": name, "status": "unreachable", "http": 0, "error": str(e)[:120]}

    async def _probe_n2yo() -> dict:
        if not n2yo_key:
            return {"source": "n2yo", "status": "not_configured", "note": "Set N2YO_API_KEY env var"}
        # Test with ISS (NORAD 25544)
        url = f"https://api.n2yo.com/rest/v1/satellite/tle/25544&apiKey={n2yo_key}"
        try:
            async with _httpx.AsyncClient(timeout=8.0, follow_redirects=True) as c:
                r = await c.get(url)
                if r.status_code == 200:
                    data = r.json()
                    has_tle = bool(data.get("tle", "").strip())
                    return {"source": "n2yo", "status": "ok", "http": 200, "has_tle": has_tle,
                            "sat_name": data.get("info", {}).get("satname", "?")}
                return {"source": "n2yo", "status": "error", "http": r.status_code}
        except Exception as e:
            return {"source": "n2yo", "status": "unreachable", "http": 0, "error": str(e)[:120]}

    results = await asyncio.gather(
        _probe_n2yo(),
        _probe_celestrak("https://celestrak.org/pub/TLE/stations.txt", "celestrak-stations"),
        _probe_celestrak("https://celestrak.org/pub/TLE/weather.txt", "celestrak-weather"),
        _probe_celestrak("https://celestrak.org/pub/TLE/gps-ops.txt", "celestrak-gps"),
    )
    reachable = [r for r in results if r.get("status") == "ok"]
    return {
        "sources": list(results),
        "n2yo_configured": bool(n2yo_key),
        "reachable": len(reachable),
        "active_source": "n2yo+sgp4" if n2yo_key and results[0].get("status") == "ok" else "celestrak+sgp4",
        "curated_satellites": 32,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/health", tags=["osint"])
async def get_health():
    """
    Health alerts and disease outbreaks from WHO RSS, CDC, and ReliefWeb.
    Also returns vaccination coverage data from World Bank.
    """
    try:
        data = await _health_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("Health agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch health data: {exc}")


@app.get("/api/datacenters", tags=["osint"])
async def get_datacenters():
    """
    Data infrastructure locations: datacenters, cloud regions, and internet exchanges.
    Sources: PeeringDB API (free), static AWS/GCP/Azure region data, EpochAI datasets.
    """
    try:
        data = await _datacenter_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("Datacenter agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch datacenter data: {exc}")


@app.get("/api/social-feeds", tags=["osint"])
async def get_social_feeds():
    """
    Verified geopolitical intelligence from curated social media accounts.
    Sources: Twitter/X API v2 (set TWITTER_BEARER_TOKEN) with RSS fallback.
    Covers war, conflict, military, NATO, and geopolitical developments.
    """
    try:
        data = await _social_media_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("Social media agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch social feeds: {exc}")


@app.get("/api/news-intel", tags=["osint"])
async def get_news_intel():
    """
    Aggregated intelligence news from verified sources.
    Sources: NewsAPI (set NEWS_API_KEY) with multi-source RSS fallback.
    Categories: geopolitics, defense, conflict, cyber, diplomacy.
    """
    try:
        data = await _news_intel_agent.fetch_data()
        return data
    except Exception as exc:
        logger.error("News intel agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch news intelligence: {exc}")


@app.get("/api/osint-summary", tags=["osint"])
async def get_osint_summary():
    """
    Combined OSINT summary: all intelligence layers fetched concurrently.
    Includes flights, vessels, earthquakes, DDoS, satellites, health, and datacenters.
    """
    try:
        results = await asyncio.gather(
            _flight_agent.fetch_data(),
            _vessel_agent.fetch_data(),
            _earthquake_agent.fetch_data(),
            _ddos_agent.fetch_data(),
            _satellite_agent.fetch_data(),
            _health_agent.fetch_data(),
            _datacenter_agent.fetch_data(),
            return_exceptions=True,
        )

        labels = ["flights", "vessels", "earthquakes", "ddos", "satellites", "health", "datacenters"]

        def _safe(result, label: str):
            if isinstance(result, Exception):
                logger.error("%s failed in osint-summary: %s", label, result)
                return {"error": str(result)}
            return result

        return {
            label: _safe(result, label)
            for label, result in zip(labels, results)
        } | {"lastUpdated": datetime.now(timezone.utc).isoformat()}

    except Exception as exc:
        logger.error("OSINT summary error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch OSINT summary: {exc}")


# ---------------------------------------------------------------------------
# Dhurandhar Extended Intelligence Routes
# ---------------------------------------------------------------------------

@app.get("/api/fires", tags=["dhurandhar"])
async def get_fires():
    """
    Global active wildfire detections from NASA FIRMS (VIIRS / MODIS, 24h).
    Falls back to GDELT wildfire news if FIRMS endpoints are unreachable.
    """
    try:
        return await _fires_agent.fetch_data()
    except Exception as exc:
        logger.error("Fires agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch fires: {exc}")


@app.get("/api/internet-outages", tags=["dhurandhar"])
async def get_internet_outages():
    """
    Internet shutdown / outage reports.
    Sources: Cloudflare Radar (CF_RADAR_TOKEN), NetBlocks RSS, GDELT.
    """
    try:
        return await _internet_outage_agent.fetch_data()
    except Exception as exc:
        logger.error("Internet outage agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch outages: {exc}")


@app.get("/api/submarines", tags=["dhurandhar"])
async def get_submarines():
    """
    Known submarine bases (US, Russia, China, India, NATO, Iran, etc.) plus
    OSINT-derived deployment news. Real-time sub positions are classified
    and not publicly broadcast.
    """
    try:
        return await _submarine_agent.fetch_data()
    except Exception as exc:
        logger.error("Submarine agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch submarine data: {exc}")


@app.get("/api/drones", tags=["dhurandhar"])
async def get_drones():
    """
    Drone strike & UAV incident tracking from GDELT + The War Zone + Defense News.
    """
    try:
        return await _drone_agent.fetch_data()
    except Exception as exc:
        logger.error("Drone agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch drone data: {exc}")


@app.get("/api/cctv", tags=["dhurandhar"])
async def get_cctv():
    """
    Curated catalogue of publicly published webcams (tourism, ports, airports,
    traffic, conflict-adjacent). Only operator-released feeds are referenced.
    """
    try:
        return await _cctv_agent.fetch_data()
    except Exception as exc:
        logger.error("CCTV agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch CCTV catalogue: {exc}")


@app.get("/api/salvo", tags=["dhurandhar"])
async def get_salvo():
    """
    Iran / US / proxy conflict salvo tracker — missile and drone exchanges
    aggregated from GDELT, USNI, Naval News, The War Zone and Long War Journal.
    Includes well-documented historical salvo anchors with origin/target arcs.
    """
    try:
        return await _salvo_agent.fetch_data()
    except Exception as exc:
        logger.error("Salvo agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch salvo data: {exc}")


@app.get("/api/dhurandhar-summary", tags=["dhurandhar"])
async def get_dhurandhar_summary():
    """
    Combined Dhurandhar payload: all six extended intelligence layers fetched concurrently.
    """
    try:
        fires, outages, subs, drones, cctv, salvo = await asyncio.gather(
            _fires_agent.fetch_data(),
            _internet_outage_agent.fetch_data(),
            _submarine_agent.fetch_data(),
            _drone_agent.fetch_data(),
            _cctv_agent.fetch_data(),
            _salvo_agent.fetch_data(),
            return_exceptions=True,
        )

        def _safe(r, label):
            if isinstance(r, Exception):
                logger.error("%s failed: %s", label, r)
                return {"error": str(r)}
            return r

        return {
            "fires":          _safe(fires,   "FiresAgent"),
            "internetOutages":_safe(outages, "InternetOutageAgent"),
            "submarines":     _safe(subs,    "SubmarineAgent"),
            "drones":         _safe(drones,  "DroneAgent"),
            "cctv":           _safe(cctv,    "CCTVAgent"),
            "salvo":          _safe(salvo,   "SalvoAgent"),
            "lastUpdated":    datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.error("Dhurandhar summary error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch dhurandhar summary: {exc}")


# ---------------------------------------------------------------------------
# Claude Analyst Team Routes
# ---------------------------------------------------------------------------

async def _gather_intel_payload() -> dict:
    """
    Aggregate the OSINT swarm output into a single payload the Claude analyst
    team can reason over. Runs the agents concurrently and tolerates per-agent
    failures so a single broken feed doesn't blank the brief.
    """
    results = await asyncio.gather(
        _flight_agent.fetch_data(),
        _military_flight_agent.fetch_data(),
        _vessel_agent.fetch_data(),
        _earthquake_agent.fetch_data(),
        _satellite_agent.fetch_data(),
        _health_agent.fetch_data(),
        _datacenter_agent.fetch_data(),
        _fires_agent.fetch_data(),
        _internet_outage_agent.fetch_data(),
        _submarine_agent.fetch_data(),
        _drone_agent.fetch_data(),
        _cctv_agent.fetch_data(),
        _salvo_agent.fetch_data(),
        _protest_agent.fetch_data(),
        _hapi_agent.fetch_data(),
        _news_intel_agent.fetch_data(),
        return_exceptions=True,
    )
    labels = [
        "flights", "militaryFlights", "vessels", "earthquakes", "satellites",
        "health", "datacenters", "fires", "internetOutages", "submarines",
        "drones", "cctv", "salvo", "protests", "hapiEvents", "newsIntel",
    ]

    def _safe(r, label):
        if isinstance(r, Exception):
            logger.warning("intel payload — %s failed: %s", label, r)
            return {"error": str(r)}
        return r

    return {label: _safe(r, label) for label, r in zip(labels, results)}


def _resolve_team(engine: Optional[str] = None):
    """Map ?engine= query param → coordinator. Defaults to whatever's available."""
    if engine == "claude":
        if not claude_available():
            raise HTTPException(
                status_code=400,
                detail="engine=claude requested but ANTHROPIC_API_KEY is not set.",
            )
        return _claude_team, "claude"
    if engine == "local":
        return _local_team, "local"
    if engine is None:
        team = _active_team()
        return team, "claude" if team is _claude_team else "local"
    raise HTTPException(status_code=400, detail=f"unknown engine: {engine}")


async def _run_one_analyst(team, attr: str, raw: dict):
    """
    Run a single analyst across either team. Claude analysts expose .analyse;
    local synths expose .synthesise. We normalise here so the routes are
    engine-agnostic.
    """
    analyst = getattr(team, attr)
    if hasattr(analyst, "analyse"):
        return await analyst.analyse(raw)
    # Local synth — synchronous CPU work
    return analyst.synthesise(raw)


@app.get("/api/intel/status", tags=["intel"])
async def get_intel_status():
    """Which intel team is currently driving /api/intel/* routes?"""
    using_claude = claude_available()
    active = _active_team()
    return {
        "claudeAvailable": using_claude,
        "ollamaAvailable": ollama_available(),
        "activeEngine": "claude" if using_claude else "local",
        "countries": list(active.regional_analysts.keys()),
        "analysts": [
            "threat_analyst", "correlation_agent", "briefing_agent",
            *[f"regional_analyst:{cc}" for cc in active.regional_analysts],
        ],
        "briefingModel": active.briefing_agent.model if hasattr(active.briefing_agent, "model") else "local-heuristic-v1",
        "analystModel": active.threat_analyst.model if hasattr(active.threat_analyst, "model") else "local-heuristic-v1",
        "engines": {
            "claude": {
                "available": using_claude,
                "reason": None if using_claude else "ANTHROPIC_API_KEY not set",
            },
            "local": {"available": True, "reason": None},
            "ollama": {
                "available": ollama_available(),
                "reason": None if ollama_available() else "Ollama not detected on localhost:11434 (optional)",
            },
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/intel/team-brief", tags=["intel"])
async def get_team_brief(engine: Optional[str] = None):
    """
    Full analyst team product (briefing + threats + correlations + regional).
    Defaults to Claude if ANTHROPIC_API_KEY is set, otherwise the local
    heuristic team. Force one with ?engine=claude or ?engine=local.
    """
    team, engine_label = _resolve_team(engine)
    try:
        raw = await _gather_intel_payload()
        result = await team.run(raw)
        result.setdefault("engine", engine_label)
        return result
    except Exception as exc:
        logger.error("Team brief failed (engine=%s): %s", engine_label, exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Team brief failed: {exc}")


@app.get("/api/intel/threats", tags=["intel"])
async def get_intel_threats(engine: Optional[str] = None):
    """ThreatAnalyst / ThreatSynth output only — ranked threats list."""
    team, _ = _resolve_team(engine)
    try:
        raw = await _gather_intel_payload()
        return await _run_one_analyst(team, "threat_analyst", raw)
    except Exception as exc:
        logger.error("Threat analyst failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Threat analyst failed: {exc}")


@app.get("/api/intel/correlations", tags=["intel"])
async def get_intel_correlations(engine: Optional[str] = None):
    """CorrelationAgent / CorrelationSynth output only — cross-feed patterns."""
    team, _ = _resolve_team(engine)
    try:
        raw = await _gather_intel_payload()
        # Both engines expose .correlation_agent (Claude) or .correlation_synth (local).
        # Use whichever the team has.
        attr = "correlation_agent" if hasattr(team, "correlation_agent") else "correlation_synth"
        return await _run_one_analyst(team, attr, raw)
    except Exception as exc:
        logger.error("Correlation agent failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Correlation agent failed: {exc}")


@app.get("/api/intel/regional/{country_code}", tags=["intel"])
async def get_intel_regional(country_code: str, engine: Optional[str] = None):
    """Regional brief for a single country (US, RU, CN, IN, IR)."""
    cc = country_code.upper()
    if cc not in COUNTRY_PROFILES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported country code: {country_code}. Use one of: {', '.join(COUNTRY_PROFILES)}",
        )
    team, _ = _resolve_team(engine)
    analyst = team.regional_analysts.get(cc)
    if analyst is None:
        raise HTTPException(status_code=500, detail=f"No analyst configured for {cc}")
    try:
        raw = await _gather_intel_payload()
        if hasattr(analyst, "analyse"):
            return await analyst.analyse(raw)
        return analyst.synthesise(raw)
    except Exception as exc:
        logger.error("Regional analyst %s failed: %s", cc, exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Regional analyst failed: {exc}")


# ---------------------------------------------------------------------------
# Entrypoint (for direct execution)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
