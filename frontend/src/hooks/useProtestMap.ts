import { useQuery } from '@tanstack/react-query'
import { fetchProtestMap, fetchStreams } from '../api/protests'
import type { ProtestMapResponse, StreamsResponse } from '../types/protest'

// Always fetch from real API — no demo data fallback.
// Dev: uses Vite /api proxy → localhost:8000
// Prod: uses VITE_API_BASE_URL

export function useProtestMap() {
  return useQuery<ProtestMapResponse>({
    queryKey: ['protest-map'],
    queryFn: fetchProtestMap,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 5 * 60 * 1000,
    retry: 1,
  })
}

export function useStreams() {
  return useQuery<StreamsResponse>({
    queryKey: ['streams'],
    queryFn: fetchStreams,
    staleTime: 10 * 60 * 1000,
    refetchInterval: 10 * 60 * 1000,
    retry: 1,
  })
}
