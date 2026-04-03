import { useQuery } from '@tanstack/react-query'
import { fetchProtestMap, fetchStreams } from '../api/protests'
import { DEMO_MAP_DATA } from '../data/demoData'
import type { StreamsResponse } from '../types/protest'

// When VITE_USE_DEMO=true the hook returns bundled data instantly —
// no backend server, no API calls, works on any static host (Netlify, GitHub Pages).
const IS_DEMO = import.meta.env.VITE_USE_DEMO === 'true'

export function useProtestMap() {
  return useQuery({
    queryKey: ['protest-map', IS_DEMO],
    queryFn: IS_DEMO ? () => Promise.resolve(DEMO_MAP_DATA) : fetchProtestMap,
    staleTime: IS_DEMO ? Infinity : 5 * 60 * 1000,
    refetchInterval: IS_DEMO ? false : 5 * 60 * 1000,
    retry: IS_DEMO ? 0 : 2,
  })
}

export function useStreams() {
  return useQuery({
    queryKey: ['streams', IS_DEMO],
    queryFn: IS_DEMO
      ? (): Promise<StreamsResponse> => Promise.resolve(DEMO_MAP_DATA.streams)
      : fetchStreams,
    staleTime: IS_DEMO ? Infinity : 10 * 60 * 1000,
    refetchInterval: IS_DEMO ? false : 10 * 60 * 1000,
    retry: IS_DEMO ? 0 : 2,
  })
}
