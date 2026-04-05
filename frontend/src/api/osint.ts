import axios from 'axios'
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
} from '../types/osint'

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 35_000,   // backend itself allows up to 30 s per source; give it a 5 s buffer
})

export async function fetchFlights(): Promise<FlightsResponse> {
  const { data } = await api.get<FlightsResponse>('/flights')
  return data
}

export async function fetchMilitaryFlights(): Promise<MilitaryFlightsResponse> {
  const { data } = await api.get<MilitaryFlightsResponse>('/military-flights')
  return data
}

export async function fetchVessels(): Promise<VesselsResponse> {
  const { data } = await api.get<VesselsResponse>('/vessels')
  return data
}

export async function fetchEarthquakes(): Promise<EarthquakesResponse> {
  const { data } = await api.get<EarthquakesResponse>('/earthquakes')
  return data
}

export async function fetchDDoS(): Promise<DDoSResponse> {
  const { data } = await api.get<DDoSResponse>('/ddos')
  return data
}

export async function fetchSatellites(): Promise<SatellitesResponse> {
  const { data } = await api.get<SatellitesResponse>('/satellites')
  return data
}

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/health')
  return data
}

export async function fetchDatacenters(): Promise<DatacentersResponse> {
  const { data } = await api.get<DatacentersResponse>('/datacenters')
  return data
}

export async function fetchSocialFeeds(): Promise<SocialFeedsResponse> {
  const { data } = await api.get<SocialFeedsResponse>('/social-feeds')
  return data
}

export async function fetchNewsIntel(): Promise<NewsIntelResponse> {
  const { data } = await api.get<NewsIntelResponse>('/news-intel')
  return data
}
