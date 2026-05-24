"""
OSINT Intelligence Platform - Multi-Agent System

Each agent is responsible for fetching and processing data
from a specific domain using real external APIs.
"""

from .economic_agent import EconomicAgent
from .ai_infra_agent import AIInfraAgent
from .infrastructure_agent import InfrastructureAgent
from .defense_agent import DefenseAgent
from .news_agent import NewsAgent
from .protest_agent import ProtestAgent
from .hapi_agent import HAPIAgent
from .stream_agent import StreamAgent

# New OSINT intelligence agents
from .flight_agent import FlightAgent
from .military_flight_agent import MilitaryFlightAgent
from .vessel_agent import VesselAgent
from .earthquake_agent import EarthquakeAgent
from .ddos_agent import DDoSAgent
from .satellite_agent import SatelliteAgent
from .health_agent import HealthAgent
from .datacenter_agent import DatacenterAgent
from .social_media_agent import SocialMediaAgent
from .news_intel_agent import NewsIntelAgent

# Dhurandhar branch — extended intelligence agents
from .fires_agent import FiresAgent
from .internet_outage_agent import InternetOutageAgent
from .submarine_agent import SubmarineAgent
from .drone_agent import DroneAgent
from .cctv_agent import CCTVAgent
from .salvo_agent import SalvoAgent

__all__ = [
    # Existing agents
    "EconomicAgent",
    "AIInfraAgent",
    "InfrastructureAgent",
    "DefenseAgent",
    "NewsAgent",
    "ProtestAgent",
    "HAPIAgent",
    "StreamAgent",
    # New OSINT agents
    "FlightAgent",
    "MilitaryFlightAgent",
    "VesselAgent",
    "EarthquakeAgent",
    "DDoSAgent",
    "SatelliteAgent",
    "HealthAgent",
    "DatacenterAgent",
    "SocialMediaAgent",
    "NewsIntelAgent",
    # Dhurandhar extended agents
    "FiresAgent",
    "InternetOutageAgent",
    "SubmarineAgent",
    "DroneAgent",
    "CCTVAgent",
    "SalvoAgent",
]
