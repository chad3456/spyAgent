import axios from 'axios'
import type {
  ProtestsResponse,
  HAPIResponse,
  StreamsResponse,
  ProtestMapResponse,
} from '../types/protest'

// In production (Netlify), set VITE_API_BASE_URL to your Render backend URL:
//   https://<your-render-service>.onrender.com/api
// In development, falls back to the Vite proxy (/api → localhost:8000/api).
const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api'

const api = axios.create({
  baseURL: API_BASE,
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
