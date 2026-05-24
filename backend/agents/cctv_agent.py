"""
CCTV OSINT Agent — public live cameras and webcam feeds.

This agent only references KNOWN PUBLIC webcams that operators have voluntarily
made open (tourism, traffic, weather, ports, airports). It does NOT scrape
unsecured private cameras or anything resembling Insecam-style indexing.

Sources:
  - Curated catalogue of publicly published webcams (EarthCam, Windy, port
    authority feeds, government traffic cameras with open embeds).

Returns a feed list with embed URLs, geolocation, category, and operator.
"""

import logging
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Curated, publicly published webcams. All operators have intentionally
# released these feeds for public viewing.
PUBLIC_CAMERAS: list[dict] = [
    # Cities — tourism / landmark
    {"id": "nyc-times-sq",   "name": "Times Square, New York",    "lat": 40.7580, "lon": -73.9855, "country": "US", "category": "city",     "operator": "EarthCam",        "url": "https://www.earthcam.com/usa/newyork/timessquare/?cam=tsstreet"},
    {"id": "tokyo-shibuya",  "name": "Shibuya Crossing, Tokyo",   "lat": 35.6595, "lon": 139.7004, "country": "JP", "category": "city",     "operator": "Shibuya Open",    "url": "https://www.youtube.com/embed/3kPH7kTphnE?autoplay=1&mute=1"},
    {"id": "london-tower",   "name": "Tower Bridge, London",      "lat": 51.5055, "lon": -0.0754,  "country": "GB", "category": "city",     "operator": "EarthCam",        "url": "https://www.earthcam.com/uk/england/london/towerbridge/"},
    {"id": "paris-eiffel",   "name": "Eiffel Tower, Paris",       "lat": 48.8584, "lon": 2.2945,   "country": "FR", "category": "city",     "operator": "Skyline Webcams", "url": "https://www.skylinewebcams.com/en/webcam/france/ile-de-france/paris/tour-eiffel.html"},
    {"id": "moscow-red-sq",  "name": "Red Square, Moscow",        "lat": 55.7539, "lon": 37.6208,  "country": "RU", "category": "city",     "operator": "MosCam",          "url": "https://www.skylinewebcams.com/en/webcam/russian-federation/moscow/moscow/cremlino.html"},
    {"id": "delhi-india-gate","name": "India Gate, New Delhi",     "lat": 28.6129, "lon": 77.2295,  "country": "IN", "category": "city",     "operator": "Delhi Tourism",   "url": "https://www.youtube.com/embed/H1c2HPbJ7gQ?autoplay=1&mute=1"},
    {"id": "beijing-tiananmen","name": "Tiananmen Square, Beijing","lat": 39.9054, "lon": 116.3976,"country": "CN", "category": "city",     "operator": "CGTN Live",       "url": "https://www.youtube.com/embed/4G6QDNC4jPs?autoplay=1&mute=1"},

    # Ports / maritime
    {"id": "port-rotterdam", "name": "Port of Rotterdam",         "lat": 51.9536, "lon": 4.1396,   "country": "NL", "category": "port",     "operator": "Port Authority",  "url": "https://www.portofrotterdam.com/en/about-port-authority/news-and-press-releases/webcams"},
    {"id": "port-singapore", "name": "Port of Singapore",         "lat": 1.2640,  "lon": 103.8200, "country": "SG", "category": "port",     "operator": "MPA Singapore",   "url": "https://www.mpa.gov.sg/web/portal/home/port-of-singapore"},
    {"id": "port-la",        "name": "Port of Los Angeles",       "lat": 33.7395, "lon": -118.2616,"country": "US", "category": "port",     "operator": "POLA",            "url": "https://www.portoflosangeles.org/about/port-cam"},
    {"id": "suez-canal",     "name": "Suez Canal Authority",      "lat": 30.5832, "lon": 32.2776,  "country": "EG", "category": "port",     "operator": "SCA",             "url": "https://www.suezcanal.gov.eg/English/Pages/default.aspx"},

    # Airports
    {"id": "airport-jfk",    "name": "JFK Airport Tower",         "lat": 40.6413, "lon": -73.7781, "country": "US", "category": "airport",  "operator": "AirportWebcams",  "url": "https://www.airportwebcams.net/jfk-john-f-kennedy-international-airport-webcam/"},
    {"id": "airport-lhr",    "name": "London Heathrow",            "lat": 51.4700, "lon": -0.4543,  "country": "GB", "category": "airport",  "operator": "AirportWebcams",  "url": "https://www.airportwebcams.net/london-heathrow-airport-webcam/"},
    {"id": "airport-dxb",    "name": "Dubai International",        "lat": 25.2532, "lon": 55.3657,  "country": "AE", "category": "airport",  "operator": "AirportWebcams",  "url": "https://www.airportwebcams.net/dubai-international-airport-webcam/"},

    # Borders / strategic checkpoints
    {"id": "border-tijuana", "name": "San Ysidro / Tijuana POE",   "lat": 32.5419, "lon": -117.0297,"country": "US", "category": "border",   "operator": "CBP",             "url": "https://bwt.cbp.gov/index.html"},
    {"id": "border-rafah",   "name": "Rafah Crossing area",        "lat": 31.2840, "lon": 34.2470,  "country": "EG", "category": "border",   "operator": "Skyline",         "url": "https://www.skylinewebcams.com/"},

    # Weather / strategic geography
    {"id": "weather-icel",   "name": "Iceland Volcano Cam",        "lat": 63.9000, "lon": -22.4000, "country": "IS", "category": "weather",  "operator": "RUV / mbl.is",    "url": "https://www.youtube.com/embed/T8gFhdq3p4U?autoplay=1&mute=1"},
    {"id": "weather-everest","name": "Mt Everest Base Camp",       "lat": 27.9881, "lon": 86.9250,  "country": "NP", "category": "weather",  "operator": "Mountaineering",  "url": "https://www.youtube.com/embed/iC91zFcc4Hw?autoplay=1&mute=1"},

    # Conflict-adjacent (publicly broadcast)
    {"id": "kyiv-maidan",    "name": "Maidan Square, Kyiv",        "lat": 50.4501, "lon": 30.5234,  "country": "UA", "category": "conflict", "operator": "Kyiv City Cam",   "url": "https://www.youtube.com/embed/3CdpYEMM8eY?autoplay=1&mute=1"},
    {"id": "jerusalem-old",  "name": "Old City, Jerusalem",        "lat": 31.7767, "lon": 35.2345,  "country": "IL", "category": "conflict", "operator": "EarthCam",        "url": "https://www.earthcam.com/world/israel/jerusalem/?cam=jerusalem"},

    # Russia
    {"id": "spb-palace-sq",  "name": "Palace Square, St Petersburg","lat": 59.9398,"lon": 30.3146,  "country": "RU", "category": "city",     "operator": "Skyline",         "url": "https://www.skylinewebcams.com/en/webcam/russian-federation/saint-petersburg/saint-petersburg.html"},
]


class CCTVAgent(BaseAgent):
    cache_prefix = "cctv"

    async def fetch_data(self) -> dict:
        # Pull OSINT video imagery news in the background — CCTV-related
        # geolocation analysis stories from open-source investigators.
        try:
            news = await self.fetch_gdelt(
                "(\"CCTV footage\" OR \"surveillance video\" OR \"geolocated\") AND (OSINT OR investigation)",
                max_records=10,
                category="cctv-osint",
            )
        except Exception as exc:
            logger.info("CCTV OSINT news fetch failed: %s", exc)
            news = []

        by_category: dict[str, int] = {}
        by_country: dict[str, int] = {}
        for cam in PUBLIC_CAMERAS:
            by_category[cam["category"]] = by_category.get(cam["category"], 0) + 1
            by_country[cam["country"]] = by_country.get(cam["country"], 0) + 1

        return {
            "cameras": PUBLIC_CAMERAS,
            "news": news,
            "summary": {
                "total": len(PUBLIC_CAMERAS),
                "byCategory": by_category,
                "byCountry": by_country,
            },
            "disclaimer": (
                "All cameras listed are publicly published by their operators "
                "(tourism boards, port authorities, news broadcasters, etc.). "
                "No private/unsecured cameras are referenced."
            ),
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }
