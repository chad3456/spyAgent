import { useQuery } from '@tanstack/react-query'
import { fetchProtestMap, fetchStreams } from '../api/protests'
import { DEMO_MAP_DATA } from '../data/demoData'
import type { ProtestMapResponse, StreamsResponse } from '../types/protest'

// Use demo data when:
//  1. No backend URL has been configured (pure static Netlify deploy), OR
//  2. VITE_USE_DEMO is explicitly set to "true"
// This means the app always shows data — it never shows a blank map.
const HAS_BACKEND = Boolean(import.meta.env.VITE_API_BASE_URL)
const IS_DEMO = !HAS_BACKEND || import.meta.env.VITE_USE_DEMO === 'true'

async function fetchWithDemoFallback(): Promise<ProtestMapResponse> {
  if (IS_DEMO) return DEMO_MAP_DATA
  try {
    return await fetchProtestMap()
  } catch {
    // Backend unreachable — fall back to demo data silently
    return DEMO_MAP_DATA
  }
}

async function fetchStreamsWithFallback(): Promise<StreamsResponse> {
  if (IS_DEMO) return DEMO_MAP_DATA.streams
  try {
    return await fetchStreams()
  } catch {
    return DEMO_MAP_DATA.streams
  }
}

export function useProtestMap() {
  return useQuery({
    queryKey: ['protest-map'],
    queryFn: fetchWithDemoFallback,
    staleTime: IS_DEMO ? Infinity : 5 * 60 * 1000,
    refetchInterval: IS_DEMO ? false : 5 * 60 * 1000,
    retry: 0, // fallback handled inside queryFn — no React Query retries needed
  })
}

export function useStreams() {
  return useQuery({
    queryKey: ['streams'],
    queryFn: fetchStreamsWithFallback,
    staleTime: IS_DEMO ? Infinity : 10 * 60 * 1000,
    refetchInterval: IS_DEMO ? false : 10 * 60 * 1000,
    retry: 0,
  })
}
