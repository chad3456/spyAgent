"""
India Progress Dashboard - FastAPI Backend
==========================================

Multi-agent system that aggregates real-time data from:
  - World Bank Open API
  - IMF DataMapper API
  - GDELT News API
  - Multiple RSS feeds (Economic Times, PIB, Business Standard)
  - Optional: NewsAPI, GNews (via env vars)

Run with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

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
from agents import EconomicAgent, AIInfraAgent, InfrastructureAgent, DefenseAgent, NewsAgent

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="India Progress Dashboard API",
    description=(
        "Real-time data aggregation API for tracking India's economic, "
        "technological, infrastructure, and defense progress."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow all origins for development (tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Agent singletons (shared cache)
# ---------------------------------------------------------------------------
_timeout = float(os.environ.get("REQUEST_TIMEOUT", "30"))
_economic_agent = EconomicAgent(timeout=_timeout)
_ai_infra_agent = AIInfraAgent(timeout=_timeout)
_infrastructure_agent = InfrastructureAgent(timeout=_timeout)
_defense_agent = DefenseAgent(timeout=_timeout)
_news_agent = NewsAgent(timeout=_timeout)


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
# Entrypoint (for direct execution)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
