"""
TeamCoordinator — runs the Claude analyst team against the aggregated OSINT
swarm payload and returns a single bundled result.

Flow:
  1. Run ThreatAnalyst + 5 RegionalAnalysts + CorrelationAgent in parallel
     (each is its own Anthropic API call — Haiku 4.5, sub-second).
  2. Feed all of their outputs into BriefingAgent (Opus 4.7 + adaptive thinking)
     for the top-level executive brief.

The whole thing is cached for 5 minutes per unique data signature.
"""

import asyncio
import logging
from datetime import datetime, timezone

from .base_analyst import claude_available
from .briefing_agent import BriefingAgent
from .correlation_agent import CorrelationAgent
from .regional_analyst import COUNTRY_PROFILES, RegionalAnalyst
from .threat_analyst import ThreatAnalyst

logger = logging.getLogger(__name__)


class TeamCoordinator:
    def __init__(self, countries: list[str] | None = None):
        self.countries = countries or ["US", "RU", "CN", "IN", "IR"]
        self.threat_analyst = ThreatAnalyst()
        self.correlation_agent = CorrelationAgent()
        self.regional_analysts = {
            cc: RegionalAnalyst(cc) for cc in self.countries if cc in COUNTRY_PROFILES
        }
        self.briefing_agent = BriefingAgent()

    async def run(self, raw_data: dict) -> dict:
        """Run the full team. `raw_data` is the aggregated swarm payload."""
        if not claude_available():
            return {
                "disabled": True,
                "reason": (
                    "ANTHROPIC_API_KEY is not configured. The Claude analyst "
                    "team is offline; raw swarm data is still available via the "
                    "other /api routes."
                ),
                "generatedAt": datetime.now(timezone.utc).isoformat(),
            }

        # Round 1 — analysts run in parallel.
        regional_tasks = {
            cc: analyst.analyse(raw_data)
            for cc, analyst in self.regional_analysts.items()
        }
        threat_task = self.threat_analyst.analyse(raw_data)
        correlation_task = self.correlation_agent.analyse(raw_data)

        threats, correlations, *regional_results = await asyncio.gather(
            threat_task,
            correlation_task,
            *regional_tasks.values(),
            return_exceptions=True,
        )

        def _safe(r, label):
            if isinstance(r, Exception):
                logger.error("%s failed: %s", label, r)
                return {"error": str(r), "analyst": label}
            return r

        threats = _safe(threats, "threat_analyst")
        correlations = _safe(correlations, "correlation_agent")

        regional: dict[str, dict] = {}
        for cc, result in zip(regional_tasks.keys(), regional_results):
            regional[cc] = _safe(result, f"regional_analyst:{cc}")

        # Round 2 — briefing agent synthesises everyone.
        analyst_bundle = {
            "threats": threats.get("analysis") if isinstance(threats, dict) else None,
            "correlations": correlations.get("analysis") if isinstance(correlations, dict) else None,
            "regional": {
                cc: (r.get("analysis") if isinstance(r, dict) else None)
                for cc, r in regional.items()
            },
        }
        briefing = await self.briefing_agent.analyse(analyst_bundle)

        # Roll up token usage so the dashboard can show what the team cost.
        def _usage(r):
            if not isinstance(r, dict):
                return {}
            return r.get("usage", {}) or {}

        total_input = (
            _usage(threats).get("inputTokens", 0)
            + _usage(correlations).get("inputTokens", 0)
            + sum(_usage(r).get("inputTokens", 0) for r in regional.values())
            + _usage(briefing).get("inputTokens", 0)
        )
        total_output = (
            _usage(threats).get("outputTokens", 0)
            + _usage(correlations).get("outputTokens", 0)
            + sum(_usage(r).get("outputTokens", 0) for r in regional.values())
            + _usage(briefing).get("outputTokens", 0)
        )
        total_cache_read = (
            _usage(threats).get("cacheReadInputTokens", 0)
            + _usage(correlations).get("cacheReadInputTokens", 0)
            + sum(_usage(r).get("cacheReadInputTokens", 0) for r in regional.values())
            + _usage(briefing).get("cacheReadInputTokens", 0)
        )

        return {
            "briefing": briefing,
            "threats": threats,
            "correlations": correlations,
            "regional": regional,
            "teamUsage": {
                "totalInputTokens": total_input,
                "totalOutputTokens": total_output,
                "totalCacheReadInputTokens": total_cache_read,
                "analystCount": 2 + len(self.regional_analysts) + 1,
            },
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        }
