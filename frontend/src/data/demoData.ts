/**
 * Embedded demo data — used when VITE_USE_DEMO=true.
 * The frontend serves this directly with zero backend calls.
 * Covers 20 protest events across 15+ countries + 8 HAPI events.
 */
import type {
  ProtestEvent,
  HAPIEvent,
  LiveStream,
  ProtestImage,
  ProtestMapResponse,
} from '../types/protest'

const now = new Date()
const ago = (h: number) => new Date(now.getTime() - h * 3600_000).toISOString()
const daysAgo = (d: number) => new Date(now.getTime() - d * 86400_000).toISOString().slice(0, 10)

// ─── GDELT-style protest events ───────────────────────────────────────────────
const DEMO_PROTESTS: ProtestEvent[] = [
  { id: 'demo-001', title: 'Thousands march in Paris against pension reform cuts', url: 'https://www.bbc.com/news/world-europe', source: 'bbc.com', sourcecountry: 'France', publishedAt: ago(1), image: null, lat: 48.8566, lon: 2.3522, country: 'France', threatLevel: 'HIGH', eventType: 'Protest', dataSource: 'GDELT', language: 'English', notes: 'Police deployed water cannons as demonstrators blocked major intersections in central Paris.' },
  { id: 'demo-002', title: 'Anti-government protests erupt in Dhaka over election results', url: 'https://www.reuters.com/world/asia-pacific', source: 'reuters.com', sourcecountry: 'Bangladesh', publishedAt: ago(2), image: null, lat: 23.8103, lon: 90.4125, country: 'Bangladesh', threatLevel: 'CRITICAL', eventType: 'Riot', dataSource: 'GDELT', language: 'English', fatalities: 3, notes: 'Clashes between protesters and security forces reported. 3 fatalities confirmed.' },
  { id: 'demo-003', title: "Workers' strike shuts down ports across Argentina", url: 'https://apnews.com', source: 'apnews.com', sourcecountry: 'Argentina', publishedAt: ago(3), image: null, lat: -34.6037, lon: -58.3816, country: 'Argentina', threatLevel: 'MEDIUM', eventType: 'Strike', dataSource: 'GDELT', language: 'English' },
  { id: 'demo-004', title: 'Pro-democracy rally draws 50,000 in Seoul', url: 'https://www.aljazeera.com/news', source: 'aljazeera.com', sourcecountry: 'South Korea', publishedAt: ago(4), image: null, lat: 37.5665, lon: 126.9780, country: 'South Korea', threatLevel: 'LOW', eventType: 'Rally', dataSource: 'GDELT', language: 'English' },
  { id: 'demo-005', title: 'Violent clashes as farmers block highways in India', url: 'https://timesofindia.indiatimes.com', source: 'timesofindia.com', sourcecountry: 'India', publishedAt: ago(2), image: null, lat: 28.6139, lon: 77.2090, country: 'India', threatLevel: 'HIGH', eventType: 'Protest', dataSource: 'GDELT', language: 'English' },
  { id: 'demo-006', title: 'Climate protesters block London Bridge for third day', url: 'https://www.theguardian.com/environment', source: 'theguardian.com', sourcecountry: 'United Kingdom', publishedAt: ago(5), image: null, lat: 51.5074, lon: -0.1278, country: 'United Kingdom', threatLevel: 'LOW', eventType: 'Demonstration', dataSource: 'GDELT', language: 'English' },
  { id: 'demo-007', title: 'Mass protests against president continue in Nairobi', url: 'https://www.reuters.com/world/africa', source: 'reuters.com', sourcecountry: 'Kenya', publishedAt: ago(6), image: null, lat: -1.2921, lon: 36.8219, country: 'Kenya', threatLevel: 'HIGH', eventType: 'Protest', dataSource: 'GDELT', language: 'English' },
  { id: 'demo-008', title: 'Gaza solidarity march in Washington DC draws tens of thousands', url: 'https://apnews.com', source: 'apnews.com', sourcecountry: 'United States', publishedAt: ago(7), image: null, lat: 38.8951, lon: -77.0364, country: 'United States', threatLevel: 'MEDIUM', eventType: 'March', dataSource: 'GDELT', language: 'English' },
  { id: 'demo-009', title: 'Protesters storm parliament building in Tbilisi', url: 'https://www.euronews.com', source: 'euronews.com', sourcecountry: 'Georgia', publishedAt: ago(8), image: null, lat: 41.6938, lon: 44.8015, country: 'Georgia', threatLevel: 'CRITICAL', eventType: 'Riot', dataSource: 'GDELT', language: 'English', fatalities: 1 },
  { id: 'demo-010', title: 'Anti-austerity protests in Athens turn violent near parliament', url: 'https://www.ekathimerini.com', source: 'ekathimerini.com', sourcecountry: 'Greece', publishedAt: ago(9), image: null, lat: 37.9838, lon: 23.7275, country: 'Greece', threatLevel: 'HIGH', eventType: 'Protest', dataSource: 'GDELT', language: 'English' },
  { id: 'demo-011', title: 'Protests in Tehran over water shortage and economic crisis', url: 'https://www.bbc.com/persian', source: 'bbc.com', sourcecountry: 'Iran', publishedAt: ago(10), image: null, lat: 35.6892, lon: 51.3890, country: 'Iran', threatLevel: 'HIGH', eventType: 'Protest', dataSource: 'GDELT', language: 'English' },
  { id: 'demo-012', title: 'Teachers strike in Mexico City demanding pay rise', url: 'https://www.reuters.com', source: 'reuters.com', sourcecountry: 'Mexico', publishedAt: ago(11), image: null, lat: 19.4326, lon: -99.1332, country: 'Mexico', threatLevel: 'MEDIUM', eventType: 'Strike', dataSource: 'GDELT', language: 'English' },
  { id: 'demo-013', title: 'University students protest in Cairo against government crackdown', url: 'https://www.aljazeera.com', source: 'aljazeera.com', sourcecountry: 'Egypt', publishedAt: ago(12), image: null, lat: 30.0444, lon: 31.2357, country: 'Egypt', threatLevel: 'MEDIUM', eventType: 'Protest', dataSource: 'GDELT', language: 'English' },
  { id: 'demo-014', title: "Truckers' strike paralyses São Paulo highways", url: 'https://www.folha.uol.com.br', source: 'folha.uol.com.br', sourcecountry: 'Brazil', publishedAt: ago(3), image: null, lat: -23.5505, lon: -46.6333, country: 'Brazil', threatLevel: 'MEDIUM', eventType: 'Strike', dataSource: 'GDELT', language: 'Portuguese' },
  { id: 'demo-015', title: 'Anti-coup protesters fired on in Myanmar — dozens injured', url: 'https://www.reuters.com/world/asia', source: 'reuters.com', sourcecountry: 'Myanmar', publishedAt: ago(1), image: null, lat: 16.8661, lon: 96.1951, country: 'Myanmar', threatLevel: 'CRITICAL', eventType: 'Violent Protest', dataSource: 'GDELT', language: 'English', fatalities: 2 },
  { id: 'demo-016', title: 'Fuel price protests spread across Nigerian cities', url: 'https://www.vanguardngr.com', source: 'vanguardngr.com', sourcecountry: 'Nigeria', publishedAt: ago(4), image: null, lat: 9.0820, lon: 8.6753, country: 'Nigeria', threatLevel: 'HIGH', eventType: 'Protest', dataSource: 'GDELT', language: 'English' },
  { id: 'demo-017', title: 'Hundreds rally in Kyiv for faster EU integration', url: 'https://www.kyivpost.com', source: 'kyivpost.com', sourcecountry: 'Ukraine', publishedAt: ago(5), image: null, lat: 50.4501, lon: 30.5234, country: 'Ukraine', threatLevel: 'LOW', eventType: 'Rally', dataSource: 'GDELT', language: 'English' },
  { id: 'demo-018', title: 'Hong Kong pro-democracy vigil draws silent crowd', url: 'https://www.scmp.com', source: 'scmp.com', sourcecountry: 'Hong Kong', publishedAt: ago(6), image: null, lat: 22.3193, lon: 114.1694, country: 'Hong Kong', threatLevel: 'LOW', eventType: 'Vigil', dataSource: 'GDELT', language: 'English' },
  { id: 'demo-019', title: 'Demonstrations in Islamabad over economic crisis intensify', url: 'https://www.dawn.com', source: 'dawn.com', sourcecountry: 'Pakistan', publishedAt: ago(7), image: null, lat: 33.7294, lon: 73.0931, country: 'Pakistan', threatLevel: 'HIGH', eventType: 'Demonstration', dataSource: 'GDELT', language: 'English' },
  { id: 'demo-020', title: 'Yellow Vest-style protests return to streets of Lyon', url: 'https://www.lemonde.fr', source: 'lemonde.fr', sourcecountry: 'France', publishedAt: ago(14), image: null, lat: 45.7640, lon: 4.8357, country: 'France', threatLevel: 'MEDIUM', eventType: 'Protest', dataSource: 'GDELT', language: 'French' },
  { id: 'demo-021', title: 'Protests against military rule erupt in Bamako', url: 'https://www.rfi.fr', source: 'rfi.fr', sourcecountry: 'Mali', publishedAt: ago(16), image: null, lat: 12.6392, lon: -8.0029, country: 'Mali', threatLevel: 'HIGH', eventType: 'Protest', dataSource: 'GDELT', language: 'French' },
  { id: 'demo-022', title: 'Hundreds arrested in Minsk as protests resume', url: 'https://www.bbc.com', source: 'bbc.com', sourcecountry: 'Belarus', publishedAt: ago(18), image: null, lat: 53.9045, lon: 27.5615, country: 'Belarus', threatLevel: 'CRITICAL', eventType: 'Protest', dataSource: 'GDELT', language: 'English', fatalities: 0 },
  { id: 'demo-023', title: 'Colombian students march against education cuts', url: 'https://www.eltiempo.com', source: 'eltiempo.com', sourcecountry: 'Colombia', publishedAt: ago(20), image: null, lat: 4.7110, lon: -74.0721, country: 'Colombia', threatLevel: 'LOW', eventType: 'March', dataSource: 'GDELT', language: 'Spanish' },
  { id: 'demo-024', title: 'Protests erupt in Jakarta over fuel subsidy cuts', url: 'https://www.thejakartapost.com', source: 'thejakartapost.com', sourcecountry: 'Indonesia', publishedAt: ago(22), image: null, lat: -6.2088, lon: 106.8456, country: 'Indonesia', threatLevel: 'MEDIUM', eventType: 'Protest', dataSource: 'GDELT', language: 'English' },
  { id: 'demo-025', title: 'Thousands demonstrate in Caracas against government', url: 'https://www.reuters.com', source: 'reuters.com', sourcecountry: 'Venezuela', publishedAt: ago(5), image: null, lat: 10.4806, lon: -66.9036, country: 'Venezuela', threatLevel: 'HIGH', eventType: 'Demonstration', dataSource: 'GDELT', language: 'English' },
]

// ─── HAPI / OCHA conflict events ──────────────────────────────────────────────
const DEMO_HAPI_EVENTS: HAPIEvent[] = [
  { id: 'hapi-eth-001', country: 'Ethiopia', countryCode: 'ETH', admin1: 'Oromia', eventType: 'Protests', eventCount: 28, fatalities: 4, date: daysAgo(2), lat: 9.1450, lon: 40.4897, threatLevel: 'CRITICAL', dataSource: 'HAPI/OCHA' },
  { id: 'hapi-sdn-001', country: 'Sudan', countryCode: 'SDN', admin1: 'Khartoum', eventType: 'Protests', eventCount: 15, fatalities: 2, date: daysAgo(1), lat: 15.5007, lon: 32.5599, threatLevel: 'CRITICAL', dataSource: 'HAPI/OCHA' },
  { id: 'hapi-hti-001', country: 'Haiti', countryCode: 'HTI', admin1: 'Ouest', eventType: 'Protests', eventCount: 22, fatalities: 6, date: daysAgo(1), lat: 18.5944, lon: -72.3074, threatLevel: 'CRITICAL', dataSource: 'HAPI/OCHA' },
  { id: 'hapi-som-001', country: 'Somalia', countryCode: 'SOM', admin1: 'Mogadishu', eventType: 'Protests', eventCount: 5, fatalities: 3, date: daysAgo(1), lat: 2.0469, lon: 45.3182, threatLevel: 'CRITICAL', dataSource: 'HAPI/OCHA' },
  { id: 'hapi-ven-001', country: 'Venezuela', countryCode: 'VEN', admin1: 'Caracas D.C.', eventType: 'Protests', eventCount: 18, fatalities: 1, date: daysAgo(2), lat: 10.4806, lon: -66.9036, threatLevel: 'HIGH', dataSource: 'HAPI/OCHA' },
  { id: 'hapi-nga-001', country: 'Nigeria', countryCode: 'NGA', admin1: 'Lagos', eventType: 'Protests', eventCount: 12, fatalities: 0, date: daysAgo(4), lat: 6.5244, lon: 3.3792, threatLevel: 'MEDIUM', dataSource: 'HAPI/OCHA' },
  { id: 'hapi-irq-001', country: 'Iraq', countryCode: 'IRQ', admin1: 'Baghdad', eventType: 'Protests', eventCount: 8, fatalities: 0, date: daysAgo(3), lat: 33.3152, lon: 44.3661, threatLevel: 'MEDIUM', dataSource: 'HAPI/OCHA' },
  { id: 'hapi-mli-001', country: 'Mali', countryCode: 'MLI', admin1: 'Bamako', eventType: 'Demonstrations', eventCount: 9, fatalities: 0, date: daysAgo(3), lat: 12.6392, lon: -8.0029, threatLevel: 'MEDIUM', dataSource: 'HAPI/OCHA' },
  { id: 'hapi-caf-001', country: 'Central African Republic', countryCode: 'CAF', admin1: 'Bangui', eventType: 'Protests', eventCount: 7, fatalities: 2, date: daysAgo(5), lat: 4.3947, lon: 18.5582, threatLevel: 'CRITICAL', dataSource: 'HAPI/OCHA' },
  { id: 'hapi-afg-001', country: 'Afghanistan', countryCode: 'AFG', admin1: 'Kabul', eventType: 'Protests', eventCount: 11, fatalities: 0, date: daysAgo(2), lat: 34.5553, lon: 69.2075, threatLevel: 'HIGH', dataSource: 'HAPI/OCHA' },
]

// ─── Live stream embed URLs ───────────────────────────────────────────────────
const DEMO_STREAMS: LiveStream[] = [
  { id: 'yt-s1', title: 'LIVE: Global Protests — Latest Coverage', embedUrl: 'https://www.youtube.com/embed?listType=search&list=protest+live+now+2024&autoplay=0', type: 'youtube_search', country: 'Global', thumbnail: null },
  { id: 'yt-s2', title: 'LIVE: Civil Unrest — Al Jazeera English', embedUrl: 'https://www.youtube.com/embed?listType=search&list=demonstration+live+news&autoplay=0', type: 'youtube_search', country: 'Global', thumbnail: null },
  { id: 'yt-s3', title: 'Strike Action & Labour Unrest Live', embedUrl: 'https://www.youtube.com/embed?listType=search&list=strike+news+live+2024&autoplay=0', type: 'youtube_search', country: 'Global', thumbnail: null },
  { id: 'yt-s4', title: 'Riot & Street Unrest Coverage', embedUrl: 'https://www.youtube.com/embed?listType=search&list=riot+live+stream+news&autoplay=0', type: 'youtube_search', country: 'Global', thumbnail: null },
  { id: 'yt-s5', title: 'March & Rally — BBC World News', embedUrl: 'https://www.youtube.com/embed?listType=search&list=march+protest+rally+live&autoplay=0', type: 'youtube_search', country: 'Global', thumbnail: null },
  { id: 'yt-s6', title: 'France Protests — France 24', embedUrl: 'https://www.youtube.com/embed?listType=search&list=france+protest+live&autoplay=0', type: 'youtube_search', country: 'France', thumbnail: null },
  { id: 'yt-s7', title: 'Asia Protest Coverage', embedUrl: 'https://www.youtube.com/embed?listType=search&list=asia+protest+demonstration+live&autoplay=0', type: 'youtube_search', country: 'Asia', thumbnail: null },
  { id: 'yt-s8', title: 'Africa Civil Unrest Live', embedUrl: 'https://www.youtube.com/embed?listType=search&list=africa+protest+unrest+live&autoplay=0', type: 'youtube_search', country: 'Africa', thumbnail: null },
]

// ─── OSINT images ─────────────────────────────────────────────────────────────
const DEMO_IMAGES: ProtestImage[] = [
  { url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c6/2019_Women%27s_March_Los_Angeles.jpg/640px-2019_Women%27s_March_Los_Angeles.jpg', title: "Women's March, Los Angeles", source: 'Wikimedia Commons', publishedAt: ago(2) },
  { url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/2019-2020_Hong_Kong_protests_-_Admiralty_-_20190901_-_10.jpg/640px-2019-2020_Hong_Kong_protests_-_Admiralty_-_20190901_-_10.jpg', title: 'Hong Kong protest crowd at Admiralty', source: 'Wikimedia Commons', publishedAt: ago(8) },
  { url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Proteste_Dresden_2017_03_02.jpg/640px-Proteste_Dresden_2017_03_02.jpg', title: 'Demonstration in Dresden', source: 'Wikimedia Commons', publishedAt: ago(12) },
  { url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Syrian_refugees_on_the_way_to_Hungary_-_Flickr_-_Mstyslav_Chernov-13.jpg/640px-Syrian_refugees_on_the_way_to_Hungary_-_Flickr_-_Mstyslav_Chernov-13.jpg', title: 'Protest march on highway', source: 'Wikimedia Commons', publishedAt: ago(20) },
]

// ─── Assembled response ───────────────────────────────────────────────────────
const threatSummary = DEMO_PROTESTS.reduce(
  (acc, e) => {
    acc[e.threatLevel] = (acc[e.threatLevel] ?? 0) + 1
    return acc
  },
  { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 } as Record<string, number>
)

export const DEMO_MAP_DATA: ProtestMapResponse = {
  protests: {
    events: DEMO_PROTESTS,
    totalCount: DEMO_PROTESTS.length,
    sources: ['GDELT (demo)', 'ACLED (demo)'],
    lastUpdated: now.toISOString(),
    threatSummary: { CRITICAL: threatSummary.CRITICAL, HIGH: threatSummary.HIGH, MEDIUM: threatSummary.MEDIUM, LOW: threatSummary.LOW },
  },
  hapiEvents: {
    conflictEvents: DEMO_HAPI_EVENTS,
    totalCount: DEMO_HAPI_EVENTS.length,
    lastUpdated: now.toISOString(),
  },
  streams: {
    liveStreams: DEMO_STREAMS,
    images: DEMO_IMAGES,
    lastUpdated: now.toISOString(),
  },
  lastUpdated: now.toISOString(),
}
