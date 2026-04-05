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

const HAS_BACKEND = Boolean(import.meta.env.VITE_API_BASE_URL)

function layerQuery<T>(
  key: LayerKey,
  fetchFn: () => Promise<T>,
  enabled: boolean,
  refreshInterval: number
) {
  return useQuery({
    queryKey: [key],
    queryFn: fetchFn,
    enabled: enabled && HAS_BACKEND,
    staleTime: refreshInterval,
    refetchInterval: enabled ? refreshInterval : false,
    retry: 1,
  })
}

export function useFlights(enabled: boolean) {
  return layerQuery<FlightsResponse>('flights', fetchFlights, enabled, 30_000)
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

export function useSocialFeeds(enabled: boolean) {
  return layerQuery<SocialFeedsResponse>('social_feeds', fetchSocialFeeds, enabled, 60_000)
}

export function useNewsIntel(enabled: boolean) {
  return layerQuery<NewsIntelResponse>('news_intel', fetchNewsIntel, enabled, 300_000)
}
