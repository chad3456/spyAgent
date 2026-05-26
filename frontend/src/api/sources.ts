import axios from 'axios'

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api'

const api = axios.create({ baseURL: API_BASE, timeout: 15_000 })

export interface DataSource {
  label: string
  publiclyAvailable: boolean
  envKey: string | null
  envKeySet: boolean
  mode: 'keyless-public' | 'keyless-fallback' | 'upgraded'
  fallback: string
}

export interface SourcesResponse {
  headline: string
  noKeyRequired: boolean
  sources: DataSource[]
  summary: {
    totalSources: number
    keylessSources: number
    optionalUpgrades: number
    activeUpgrades: number
  }
  timestamp: string
}

export async function fetchSources(): Promise<SourcesResponse> {
  const { data } = await api.get<SourcesResponse>('/sources')
  return data
}
