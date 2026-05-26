"""
LocalTeamCoordinator — orchestrates the local intel team.

Same interface as `agents.claude.TeamCoordinator.run(raw)` so the dashboard
endpoint can swap between them transparently.
"""
from __future__ import annotations


import asyncio
import logging
from datetime import datetime, timezone

from .briefing_synth import BriefingSynth
from .correlation_synth import CorrelationSynth
from .ollama_client import ollama_available
from .regional_synth import COUNTRY_PROFILES, RegionalSynth
from .threat_synth import ThreatSynth

logger = logging.getLogger(__name__)


class LocalTeamCoordinator:
    def __init__(self, countries: list[str] | None = None):
        self.countries = countries or ["US", "RU", "CN", "IN", "IR"]
        self.threat_synth = ThreatSynth()
        self.correlation_synth = CorrelationSynth()
        self.regional_synths = {
            cc: RegionalSynth(cc) for cc in self.countries if cc in COUNTRY_PROFILES
        }
        self.briefing_synth = BriefingSynth()

    @property
    def briefing_agent(self):
        """Compatibility shim — Claude team exposes briefing_agent.model on the panel."""
        return self.briefing_synth

    @property
    def threat_analyst(self):
        return self.threat_synth

    @property
    def regional_analysts(self):
        return self.regional_synths

    async def run(self, raw_data: dict) -> dict:
        """Run all synthesizers and return the bundled product."""
        # Round 1 — synthesizers are pure-CPU and fast; run them inline.
        threats = self.threat_synth.synthesise(raw_data)
        correlations = self.correlation_synth.synthesise(raw_data)
        regional: dict[str, dict] = {
            cc: synth.synthesise(raw_data) for cc, synth in self.regional_synths.items()
        }

        # Round 2 — briefing (may call Ollama; runs async).
        analyst_bundle = {
            "threats": threats.get("analysis"),
            "correlations": correlations.get("analysis"),
            "regional": {cc: r.get("analysis") for cc, r in regional.items()},
        }
        briefing = await self.briefing_synth.synthesise_async(analyst_bundle)

        return {
            "briefing": briefing,
            "threats": threats,
            "correlations": correlations,
            "regional": regional,
            "teamUsage": {
                "totalInputTokens": 0,
                "totalOutputTokens": 0,
                "totalCacheReadInputTokens": 0,
                "analystCount": 2 + len(self.regional_synths) + 1,
            },
            "engine": "local-heuristic",
            "ollamaActive": ollama_available(),
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        }
