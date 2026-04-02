import axios from 'axios'
import type {
  ProtestsResponse,
  HAPIResponse,
  StreamsResponse,
  ProtestMapResponse,
} from '../types/protest'

const api = axios.create({
  baseURL: '/api',
  timeout: 30_000,
})

export async function fetchProtests(): Promise<ProtestsResponse> {
  const { data } = await api.get<ProtestsResponse>('/protests')
  return data
}

export async function fetchHAPIEvents(): Promise<HAPIResponse> {
  const { data } = await api.get<HAPIResponse>('/hapi-events')
  return data
}

export async function fetchStreams(): Promise<StreamsResponse> {
  const { data } = await api.get<StreamsResponse>('/streams')
  return data
}

export async function fetchProtestMap(): Promise<ProtestMapResponse> {
  const { data } = await api.get<ProtestMapResponse>('/protest-map')
  return data
}
