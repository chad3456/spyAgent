import { useQuery } from '@tanstack/react-query'
import {
  fetchFlights,
  fetchMilitaryFlights,
  fetchVessels,
  fetchEarthquakes,
  fetchDDoS,
  fetchSatellites,
  fetchHealth,
  fetchDatacenters,
  fetchSocialFeeds,
  fetchNewsIntel,
} from '../api/osint'
import type {
  FlightsResponse,
  MilitaryFlightsResponse,
  VesselsResponse,
  EarthquakesResponse,
  DDoSResponse,
  SatellitesResponse,
  HealthResponse,
  DatacentersResponse,
  SocialFeedsResponse,
  NewsIntelResponse,
  LayerKey,
} from '../types/osint'

// Always allow fetching — dev uses the /api Vite proxy, prod uses VITE_API_BASE_URL
function layerQuery<T>(
  key: LayerKey,
  fetchFn: () => Promise<T>,
  enabled: boolean,
  refreshMs: number
) {
  return useQuery<T>({
    queryKey: [key],
    queryFn: fetchFn,
    enabled,
    staleTime: refreshMs,
    refetchInterval: enabled ? refreshMs : false,
    retry: 1,
  })
}

export function useFlights(enabled: boolean) {
  // retry: 0 — backend already tries 3 ADS-B sources internally.
  // No point retrying at the frontend level and doubling the wait time.
  return useQuery<FlightsResponse>({
    queryKey: ['flights'],
    queryFn: fetchFlights,
    enabled,
    staleTime: 30_000,
    refetchInterval: enabled ? 30_000 : false,
    retry: 0,
  })
}

export function useMilitaryFlights(enabled: boolean) {
  return layerQuery<MilitaryFlightsResponse>(
    'military_flights',
    fetchMilitaryFlights,
    enabled,
    60_000
  )
}

export function useVessels(enabled: boolean) {
  return layerQuery<VesselsResponse>('vessels', fetchVessels, enabled, 120_000)
}

export function useEarthquakes(enabled: boolean) {
  return layerQuery<EarthquakesResponse>('earthquakes', fetchEarthquakes, enabled, 300_000)
}

export function useDDoS(enabled: boolean) {
  return layerQuery<DDoSResponse>('ddos', fetchDDoS, enabled, 300_000)
}

export function useSatellites(enabled: boolean) {
  return layerQuery<SatellitesResponse>('satellites', fetchSatellites, enabled, 30_000)
}

export function useHealth(enabled: boolean) {
  return layerQuery<HealthResponse>('health', fetchHealth, enabled, 3_600_000)
}

export function useDatacenters(enabled: boolean) {
  return layerQuery<DatacentersResponse>('datacenters', fetchDatacenters, enabled, 86_400_000)
}

export function useSocialFeeds(_enabled: boolean) {
  // Always fetch social feeds — shown in the bottom ticker regardless of layer toggle
  return useQuery<SocialFeedsResponse>({
    queryKey: ['social_feeds'],
    queryFn: fetchSocialFeeds,
    enabled: true,
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: 1,
  })
}

export function useNewsIntel(enabled: boolean) {
  return layerQuery<NewsIntelResponse>('news_intel', fetchNewsIntel, enabled, 300_000)
}
