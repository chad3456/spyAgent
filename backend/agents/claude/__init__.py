"""
Claude Analyst Team — Anthropic-powered intelligence synthesis layer.

The raw swarm agents (FlightAgent, SalvoAgent, FiresAgent, ...) fetch facts
from the internet. The Claude analysts ingest those raw facts and produce
human-grade intelligence products on top:

  - ThreatAnalyst    — ranks the most acute threats in the current data
  - RegionalAnalyst  — per-country briefs (US / RU / CN / IN / IR)
  - CorrelationAgent — finds cross-feed patterns
  - BriefingAgent    — top-level executive summary (Opus 4.7)

A TeamCoordinator runs the analysts in parallel and bundles their output.
"""

from .base_analyst import BaseAnalyst, claude_available
from .threat_analyst import ThreatAnalyst
from .regional_analyst import RegionalAnalyst
from .correlation_agent import CorrelationAgent
from .briefing_agent import BriefingAgent
from .team_coordinator import TeamCoordinator

__all__ = [
    "BaseAnalyst",
    "claude_available",
    "ThreatAnalyst",
    "RegionalAnalyst",
    "CorrelationAgent",
    "BriefingAgent",
    "TeamCoordinator",
]
