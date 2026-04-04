import { useQuery } from '@tanstack/react-query'
import { fetchProtestMap, fetchStreams } from '../api/protests'
import { DEMO_MAP_DATA } from '../data/demoData'
import type { ProtestMapResponse, StreamsResponse } from '../types/protest'

// No backend URL configured = use bundled demo data.
// Boolean(undefined) = false when VITE_API_BASE_URL is not set at build time.
const HAS_BACKEND = Boolean(import.meta.env.VITE_API_BASE_URL)

// ---------------------------------------------------------------------------
// When HAS_BACKEND is false we pass `initialData` directly to useQuery.
// React Query treats initialData as already-fresh data:
//   - isLoading = false immediately (no spinner, no async lifecycle)
//   - queryFn is NEVER called (staleTime: Infinity prevents re-fetch)
//   - data is available on the very first render
// This is the safest possible approach — no env var needed, no network call.
// ---------------------------------------------------------------------------
const STATIC_DATA: ProtestMapResponse | undefined = HAS_BACKEND ? undefined : DEMO_MAP_DATA
const STATIC_STREAMS: StreamsResponse | undefined = HAS_BACKEND ? undefined : DEMO_MAP_DATA.streams

async function fetchMapWithFallback(): Promise<ProtestMapResponse> {
  try {
    return await fetchProtestMap()
  } catch {
    return DEMO_MAP_DATA
  }
}

async function fetchStreamsWithFallback(): Promise<StreamsResponse> {
  try {
    return await fetchStreams()
  } catch {
    return DEMO_MAP_DATA.streams
  }
}

export function useProtestMap() {
  return useQuery({
    queryKey: ['protest-map'],
    // queryFn is only called when HAS_BACKEND=true (initialData not set)
    queryFn: fetchMapWithFallback,
    initialData: STATIC_DATA,
    staleTime: HAS_BACKEND ? 5 * 60 * 1000 : Infinity,
    refetchInterval: HAS_BACKEND ? 5 * 60 * 1000 : false,
    retry: 0,
  })
}

export function useStreams() {
  return useQuery({
    queryKey: ['streams'],
    queryFn: fetchStreamsWithFallback,
    initialData: STATIC_STREAMS,
    staleTime: HAS_BACKEND ? 10 * 60 * 1000 : Infinity,
    refetchInterval: HAS_BACKEND ? 10 * 60 * 1000 : false,
    retry: 0,
  })
}
