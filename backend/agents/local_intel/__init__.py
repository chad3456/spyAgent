"""
Local Intel Team — heuristic, rule-based synthesis of the OSINT swarm.

Produces the same response shape as the Claude analyst team (agents/claude/)
so the dashboard works either way. No API key, no external LLM required.

If Ollama is detected on localhost:11434, the briefing prose is polished by
the local model — but the system is fully functional with pure rules.

Components:
  - ThreatSynth      → ranked threats from severity-bearing feeds
  - CorrelationSynth → cross-feed pattern matching via geo + temporal overlap
  - RegionalSynth    → per-country (US/RU/CN/IN/IR) brief
  - BriefingSynth    → executive summary assembled from the above
  - LocalTeamCoordinator orchestrates them
"""
from __future__ import annotations


from .base_synth import BaseSynth, country_bbox, haversine_km
from .threat_synth import ThreatSynth
from .correlation_synth import CorrelationSynth
from .regional_synth import RegionalSynth, COUNTRY_PROFILES
from .briefing_synth import BriefingSynth
from .coordinator import LocalTeamCoordinator
from .ollama_client import ollama_available, polish_with_ollama

__all__ = [
    "BaseSynth",
    "country_bbox",
    "haversine_km",
    "ThreatSynth",
    "CorrelationSynth",
    "RegionalSynth",
    "BriefingSynth",
    "LocalTeamCoordinator",
    "COUNTRY_PROFILES",
    "ollama_available",
    "polish_with_ollama",
]
