// ─── OSINT Layer Types ────────────────────────────────────────────────────────

export type LayerKey =
  | 'flights'
  | 'military_flights'
  | 'vessels'
  | 'earthquakes'
  | 'ddos'
  | 'satellites'
  | 'conflicts'
  | 'health'
  | 'datacenters'
  | 'social_feeds'
  | 'news_intel'
  | 'fires'
  | 'internet_outages'
  | 'submarines'
  | 'drones'
  | 'cctv'
  | 'salvo'

export interface LayerConfig {
  key: LayerKey
  label: string
  description: string
  color: string
  icon: string
  enabled: boolean
  endpoint: string
  refreshInterval: number // ms
}

export const LAYER_CONFIGS: LayerConfig[] = [
  {
    key: 'flights',
    label: 'Live Flights',
    description: 'Civil aircraft from OpenSky Network',
    color: '#64d2ff',
    icon: '✈',
    enabled: false,
    endpoint: '/flights',
    refreshInterval: 30_000,
  },
  {
    key: 'military_flights',
    label: 'Military Aircraft',
    description: 'Military aircraft via ADS-B data',
    color: '#ff2d55',
    icon: '🛩',
    enabled: false,
    endpoint: '/military-flights',
    refreshInterval: 60_000,
  },
  {
    key: 'vessels',
    label: 'Ship Tracking',
    description: 'Vessel positions from AIS data',
    color: '#30d158',
    icon: '🚢',
    enabled: false,
    endpoint: '/vessels',
    refreshInterval: 120_000,
  },
  {
    key: 'earthquakes',
    label: 'Earthquakes',
    description: 'USGS real-time seismic activity',
    color: '#ff9f0a',
    icon: '🌋',
    enabled: false,
    endpoint: '/earthquakes',
    refreshInterval: 300_000,
  },
  {
    key: 'ddos',
    label: 'DDoS Attacks',
    description: 'Cyber attack traffic by country (Cloudflare)',
    color: '#bf5af2',
    icon: '⚡',
    enabled: false,
    endpoint: '/ddos',
    refreshInterval: 300_000,
  },
  {
    key: 'satellites',
    label: 'Satellites',
    description: 'Live satellite positions (Celestrak/NASA)',
    color: '#ffd60a',
    icon: '🛰',
    enabled: false,
    endpoint: '/satellites',
    refreshInterval: 30_000,
  },
  {
    key: 'conflicts',
    label: 'Conflicts & Protests',
    description: 'Riots, protests and unrest (GDELT)',
    color: '#ff6b35',
    icon: '🔥',
    enabled: true,
    endpoint: '/protest-map',
    refreshInterval: 300_000,
  },
  {
    key: 'health',
    label: 'Health Alerts',
    description: 'Disease outbreaks & vaccination (WHO/WB)',
    color: '#ff375f',
    icon: '🏥',
    enabled: false,
    endpoint: '/health',
    refreshInterval: 3_600_000,
  },
  {
    key: 'datacenters',
    label: 'Data Infrastructure',
    description: 'Datacenters, cloud regions & IXPs',
    color: '#0a84ff',
    icon: '🖥',
    enabled: false,
    endpoint: '/datacenters',
    refreshInterval: 86_400_000,
  },
  {
    key: 'social_feeds',
    label: 'OSINT Social Feeds',
    description: 'Verified geopolitical Twitter/X intel',
    color: '#5ac8fa',
    icon: '📡',
    enabled: false,
    endpoint: '/social-feeds',
    refreshInterval: 60_000,
  },
  {
    key: 'news_intel',
    label: 'Intelligence News',
    description: 'Geopolitical & defense news (NewsAPI)',
    color: '#ffd60a',
    icon: '📰',
    enabled: false,
    endpoint: '/news-intel',
    refreshInterval: 300_000,
  },
  {
    key: 'fires',
    label: 'Wildfires',
    description: 'NASA FIRMS active fire detections (24 h)',
    color: '#ff6a00',
    icon: '🔥',
    enabled: false,
    endpoint: '/fires',
    refreshInterval: 1_800_000,
  },
  {
    key: 'internet_outages',
    label: 'Internet Outages',
    description: 'Connectivity disruptions (Cloudflare / NetBlocks)',
    color: '#5e5ce6',
    icon: '🌐',
    enabled: false,
    endpoint: '/internet-outages',
    refreshInterval: 600_000,
  },
  {
    key: 'submarines',
    label: 'Submarine Bases',
    description: 'Known SSBN / SSN base locations + OSINT deployments',
    color: '#0a84ff',
    icon: '🚢',
    enabled: false,
    endpoint: '/submarines',
    refreshInterval: 86_400_000,
  },
  {
    key: 'drones',
    label: 'Drone Activity',
    description: 'UAV strikes & incidents (GDELT / War Zone)',
    color: '#ff453a',
    icon: '🛸',
    enabled: false,
    endpoint: '/drones',
    refreshInterval: 600_000,
  },
  {
    key: 'cctv',
    label: 'Public CCTV',
    description: 'Operator-published webcam catalogue (OSINT)',
    color: '#32d74b',
    icon: '📹',
    enabled: false,
    endpoint: '/cctv',
    refreshInterval: 86_400_000,
  },
  {
    key: 'salvo',
    label: 'Iran/US Salvo',
    description: 'Missile & drone exchanges, anchors & live events',
    color: '#ff375f',
    icon: '🚀',
    enabled: false,
    endpoint: '/salvo',
    refreshInterval: 600_000,
  },
]

// ─── Per-layer data types ─────────────────────────────────────────────────────

export interface Aircraft {
  icao24: string
  callsign?: string
  country?: string
  lat: number
  lon: number
  altitude?: number | null
  velocity?: number | null
  heading?: number | null
  vertical_rate?: number | null
  squawk?: string | null
  on_ground?: boolean
}

export interface MilitaryAircraft extends Aircraft {
  military: boolean
  nation?: string
  registration?: string
  type?: string
}

export interface Vessel {
  mmsi: string
  name: string
  type: string
  lat: number
  lon: number
  speed: number
  heading: number
  destination?: string
  flag?: string
  shipType?: string
  status?: string
}

export interface Earthquake {
  id: string
  magnitude: number
  place: string
  lat: number
  lon: number
  depth: number
  time: string
  alert?: string
  tsunami: boolean
  url: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
  felt?: number
  sig?: number
}

export interface DDoSCountry {
  country: string
  countryCode: string
  lat: number
  lon: number
  attackCount: number
  bandwidth?: number
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
  trend?: 'up' | 'down' | 'stable'
}

export interface Satellite {
  name: string
  noradId: number
  lat: number
  lon: number
  altitude: number
  // velocity fields from sgp4 propagation
  velocity_kms?: number | null
  velocity_kmh?: number | null
  inclination?: number | null
  period_min?: number | null
  // Human-readable category from curated satellite list
  // e.g. "Space Station", "Earth Observation", "Weather", "Navigation",
  //      "Communications", "Commercial", "Military", "Science"
  category: string
  description?: string
  agency?: string
  orbitType?: 'LEO' | 'MEO' | 'GEO' | 'HEO'
  source?: string
}

export interface HealthOutbreak {
  id: string
  country: string
  countryCode?: string
  lat: number
  lon: number
  disease: string
  status: string
  reportDate: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
  url?: string
  description?: string
  cases?: number
  deaths?: number
}

export interface VaccinationData {
  country: string
  countryCode: string
  lat?: number
  lon?: number
  measlesRate?: number
  dptRate?: number
}

export interface DatacenterFacility {
  id: string
  name: string
  lat: number
  lon: number
  city: string
  country: string
  provider: string
  type: 'datacenter' | 'cloud' | 'exchange' | 'cable'
  tier?: number
  org?: string
}

export interface SocialFeedItem {
  id: string
  author: string
  content: string
  url: string
  publishedAt: string
  platform: 'twitter' | 'news' | 'rss'
  topic: string
  verified: boolean
  lat?: number
  lon?: number
  location?: string
}

export interface NewsArticle {
  id: string
  title: string
  source: string
  url: string
  publishedAt: string
  description?: string
  category: string
  country?: string
  lat?: number
  lon?: number
  imageUrl?: string
}

// ─── API Response types ───────────────────────────────────────────────────────

// Response types exactly match backend agent return keys

export interface FlightsResponse {
  aircraft: Aircraft[]
  total?: number
  fetchedAt?: string
}

export interface MilitaryFlightsResponse {
  aircraft: MilitaryAircraft[]
  total?: number
  fetchedAt?: string
}

export interface VesselsResponse {
  vessels: Vessel[]
  total?: number
  fetchedAt?: string
}

export interface EarthquakesResponse {
  // Backend returns "events", not "earthquakes"
  events: Earthquake[]
  total?: number
  summary?: { critical: number; high: number; tsunamiAlerts: number }
  fetchedAt?: string
}

export interface DDoSResponse {
  countries: DDoSCountry[]
  total?: number
  source?: string
  hasCFToken?: boolean
  fetchedAt?: string
}

export interface SatellitesResponse {
  satellites: Satellite[]
  total?: number
  categories?: Record<string, number>
  source?: string         // "n2yo+sgp4" | "celestrak+sgp4"
  n2yoEnabled?: boolean
  fetchedAt?: string
}

export interface HealthResponse {
  outbreaks: HealthOutbreak[]
  vaccinationData?: VaccinationData[]
  covidData?: unknown[]
  summary?: { totalOutbreaks: number; criticalOutbreaks: number; countries: number }
  fetchedAt?: string
}

export interface DatacentersResponse {
  datacenters: DatacenterFacility[]
  cloudRegions: DatacenterFacility[]
  internetExchanges: DatacenterFacility[]
  summary?: { totalDatacenters: number; totalCloudRegions: number; totalIX: number; countries: number }
  fetchedAt?: string
}

export interface SocialFeedsResponse {
  feeds: SocialFeedItem[]
  summary?: { totalPosts: number; topics: Record<string, number> }
  hasTwitter?: boolean
  fetchedAt?: string
}

export interface NewsIntelResponse {
  articles: NewsArticle[]
  categories?: Record<string, NewsArticle[]>
  summary?: { totalArticles: number; sources: string[]; lastUpdated: string }
  fetchedAt?: string
}

// ─── Dhurandhar extended types ────────────────────────────────────────────────

export interface FireDetection {
  id: string
  lat: number
  lon: number
  brightness: number
  frp: number
  confidence: string
  sensor: string
  acquired: string
  dayNight: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
}

export interface FiresResponse {
  fires: FireDetection[]
  news: { title: string; url: string; source: string; publishedAt: string }[]
  summary: { total: number; critical: number; high: number; source: string }
  source: string
  fetchedAt: string
}

export interface OutageEvent {
  id: string
  country: string
  countryCode: string
  lat: number
  lon: number
  title: string
  url: string
  source: string
  reportedAt: string
  endedAt?: string
  type: 'active' | 'resolved' | 'report'
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
}

export interface InternetOutagesResponse {
  outages: OutageEvent[]
  summary: { total: number; active: number; countries: number }
  sources: string[]
  hasCFToken: boolean
  fetchedAt: string
}

export interface SubmarineBase {
  name: string
  country: string
  lat: number
  lon: number
  type: 'SSBN' | 'SSN' | 'SSK'
  fleet: string
}

export interface SubmarineSighting {
  id: string
  title: string
  url: string
  source: string
  publishedAt: string
}

export interface SubmarinesResponse {
  bases: SubmarineBase[]
  sightings: SubmarineSighting[]
  news: {
    navalNews: { title: string; url: string; source: string; publishedAt: string }[]
    usni: { title: string; url: string; source: string; publishedAt: string }[]
  }
  summary: { totalBases: number; countries: number; ssbnBases: number; recentSightings: number }
  disclaimer: string
  fetchedAt: string
}

export interface DroneIncident {
  id: string
  title: string
  url: string
  source: string
  publishedAt: string
  lat: number
  lon: number
  region: string
  tag: string
  severity: 'HIGH' | 'MEDIUM' | 'LOW'
}

export interface DroneHotspot {
  name: string
  lat: number
  lon: number
  country: string
  tag: string
}

export interface DronesResponse {
  incidents: DroneIncident[]
  hotspots: DroneHotspot[]
  news: {
    warZone: { title: string; url: string; source: string; publishedAt: string }[]
    defense: { title: string; url: string; source: string; publishedAt: string }[]
  }
  summary: { totalIncidents: number; hotspotCount: number; highSeverity: number }
  fetchedAt: string
}

export interface PublicCamera {
  id: string
  name: string
  lat: number
  lon: number
  country: string
  category: 'city' | 'port' | 'airport' | 'border' | 'weather' | 'conflict'
  operator: string
  url: string
}

export interface CCTVResponse {
  cameras: PublicCamera[]
  news: { title: string; url: string; source: string; publishedAt: string }[]
  summary: {
    total: number
    byCategory: Record<string, number>
    byCountry: Record<string, number>
  }
  disclaimer: string
  fetchedAt: string
}

export interface SalvoEvent {
  id: string
  title: string
  url: string
  source: string
  publishedAt: string
  lat: number
  lon: number
  region: string
  category: string
  severity: 'HIGH' | 'MEDIUM' | 'LOW'
}

export interface SalvoAnchor {
  id: string
  date: string
  name: string
  origin: { name: string; lat: number; lon: number }
  target: { name: string; lat: number; lon: number }
  munitions: string
  actor: string
  severity: 'CRITICAL' | 'HIGH'
  intercepted: boolean
}

export interface SalvoResponse {
  events: SalvoEvent[]
  anchors: SalvoAnchor[]
  news: {
    warZone: { title: string; url: string; source: string; publishedAt: string }[]
    usni: { title: string; url: string; source: string; publishedAt: string }[]
    lwj: { title: string; url: string; source: string; publishedAt: string }[]
  }
  summary: { totalEvents: number; anchorEvents: number; criticalAnchors: number }
  fetchedAt: string
}

// ─── Globe point types ────────────────────────────────────────────────────────

export interface GlobePoint {
  lat: number
  lng: number
  size: number
  color: string
  label: string
  data: unknown
  layer: LayerKey
}

export interface GlobeArc {
  startLat: number
  startLng: number
  endLat: number
  endLng: number
  color: string
  label: string
}
