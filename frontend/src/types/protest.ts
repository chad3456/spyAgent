// ─── Threat Levels ────────────────────────────────────────────────────────────

export type ThreatLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'

export const THREAT_CONFIG: Record<
  ThreatLevel,
  { color: string; bg: string; border: string; pulse: boolean; label: string }
> = {
  CRITICAL: {
    color: '#ff2d55',
    bg: 'rgba(255,45,85,0.15)',
    border: '#ff2d55',
    pulse: true,
    label: 'CRITICAL',
  },
  HIGH: {
    color: '#ff6b35',
    bg: 'rgba(255,107,53,0.15)',
    border: '#ff6b35',
    pulse: true,
    label: 'HIGH',
  },
  MEDIUM: {
    color: '#ffd60a',
    bg: 'rgba(255,214,10,0.12)',
    border: '#ffd60a',
    pulse: false,
    label: 'MEDIUM',
  },
  LOW: {
    color: '#30d158',
    bg: 'rgba(48,209,88,0.12)',
    border: '#30d158',
    pulse: false,
    label: 'LOW',
  },
  INFO: {
    color: '#64d2ff',
    bg: 'rgba(100,210,255,0.12)',
    border: '#64d2ff',
    pulse: false,
    label: 'INFO',
  },
}

// ─── Protest Event ────────────────────────────────────────────────────────────

export interface ProtestEvent {
  id: string
  title: string
  url: string
  source: string
  sourcecountry: string
  publishedAt: string
  image?: string | null
  lat: number
  lon: number
  country: string
  threatLevel: ThreatLevel
  eventType: string
  dataSource: 'GDELT' | 'ACLED' | 'HAPI/OCHA' | 'Manual'
  language?: string
  notes?: string
  fatalities?: number
  eventCount?: number
  admin1?: string
}

// ─── HAPI Conflict Event ──────────────────────────────────────────────────────

export interface HAPIEvent {
  id: string
  country: string
  countryCode: string
  admin1?: string
  eventType: string
  eventCount: number
  fatalities: number
  date: string
  lat: number
  lon: number
  threatLevel: ThreatLevel
  dataSource: 'HAPI/OCHA'
}

// ─── Live Stream ──────────────────────────────────────────────────────────────

export interface LiveStream {
  id: string
  title: string
  embedUrl: string
  type: 'youtube_search' | 'youtube_live' | 'iframe'
  country: string
  thumbnail?: string | null
  query?: string
}

export interface ProtestImage {
  url: string
  title: string
  source: string
  publishedAt: string
}

// ─── API Response types ───────────────────────────────────────────────────────

export interface ThreatSummary {
  CRITICAL: number
  HIGH: number
  MEDIUM: number
  LOW: number
}

export interface ProtestsResponse {
  events: ProtestEvent[]
  totalCount: number
  sources: string[]
  lastUpdated: string
  threatSummary: ThreatSummary
}

export interface HAPIResponse {
  conflictEvents: HAPIEvent[]
  totalCount: number
  lastUpdated: string
}

export interface StreamsResponse {
  liveStreams: LiveStream[]
  images: ProtestImage[]
  lastUpdated: string
}

export interface ProtestMapResponse {
  protests: ProtestsResponse
  hapiEvents: HAPIResponse
  streams: StreamsResponse
  lastUpdated: string
}

// ─── Filter state ─────────────────────────────────────────────────────────────

export interface FilterState {
  threatLevels: ThreatLevel[]
  dataSources: string[]
  searchQuery: string
  timespan: '6h' | '24h' | '48h' | '7d'
  showHAPI: boolean
  showGDELT: boolean
}

export const DEFAULT_FILTERS: FilterState = {
  threatLevels: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
  dataSources: ['GDELT', 'ACLED', 'HAPI/OCHA'],
  searchQuery: '',
  timespan: '24h',
  showHAPI: true,
  showGDELT: true,
}
