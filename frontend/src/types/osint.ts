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
]

// ─── Per-layer data types ─────────────────────────────────────────────────────

export interface Aircraft {
  icao24: string
  callsign: string
  country: string
  lat: number
  lon: number
  altitude: number
  velocity: number
  heading: number
  vertical_rate: number
  squawk?: string
  on_ground: boolean
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
  velocity?: number
  inclination?: number
  period?: number
  type: string
  category: 'station' | 'weather' | 'navigation' | 'earth_obs' | 'military' | 'comms' | 'other'
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

export interface FlightsResponse {
  aircraft: Aircraft[]
  totalCount: number
  lastUpdated: string
}

export interface MilitaryFlightsResponse {
  aircraft: MilitaryAircraft[]
  totalCount: number
  lastUpdated: string
}

export interface VesselsResponse {
  vessels: Vessel[]
  totalCount: number
  lastUpdated: string
}

export interface EarthquakesResponse {
  earthquakes: Earthquake[]
  totalCount: number
  summary: { CRITICAL: number; HIGH: number; MEDIUM: number; LOW: number }
  lastUpdated: string
}

export interface DDoSResponse {
  countries: DDoSCountry[]
  totalAttacks: number
  topTargets: string[]
  lastUpdated: string
}

export interface SatellitesResponse {
  satellites: Satellite[]
  totalCount: number
  categories: Record<string, number>
  lastUpdated: string
}

export interface HealthResponse {
  outbreaks: HealthOutbreak[]
  vaccinationData: VaccinationData[]
  summary: { totalOutbreaks: number; criticalOutbreaks: number; countries: number }
  lastUpdated: string
}

export interface DatacentersResponse {
  datacenters: DatacenterFacility[]
  cloudRegions: DatacenterFacility[]
  internetExchanges: DatacenterFacility[]
  summary: { totalDatacenters: number; totalCloudRegions: number; totalIX: number; countries: number }
  lastUpdated: string
}

export interface SocialFeedsResponse {
  feeds: SocialFeedItem[]
  summary: { totalPosts: number; topics: Record<string, number> }
  lastUpdated: string
}

export interface NewsIntelResponse {
  articles: NewsArticle[]
  categories: Record<string, NewsArticle[]>
  summary: { totalArticles: number; sources: string[]; lastUpdated: string }
  lastUpdated: string
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
