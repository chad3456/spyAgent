"""
India Progress Dashboard - Multi-Agent System

Each agent is responsible for fetching and processing data
from a specific domain using real external APIs.
"""

from .economic_agent import EconomicAgent
from .ai_infra_agent import AIInfraAgent
from .infrastructure_agent import InfrastructureAgent
from .defense_agent import DefenseAgent
from .news_agent import NewsAgent

__all__ = [
    "EconomicAgent",
    "AIInfraAgent",
    "InfrastructureAgent",
    "DefenseAgent",
    "NewsAgent",
]
