import { useQuery } from '@tanstack/react-query'
import { fetchProtestMap, fetchStreams } from '../api/protests'

export function useProtestMap() {
  return useQuery({
    queryKey: ['protest-map'],
    queryFn: fetchProtestMap,
    staleTime: 5 * 60 * 1000,   // 5 minutes
    refetchInterval: 5 * 60 * 1000,
    retry: 2,
  })
}

export function useStreams() {
  return useQuery({
    queryKey: ['streams'],
    queryFn: fetchStreams,
    staleTime: 10 * 60 * 1000,
    refetchInterval: 10 * 60 * 1000,
    retry: 2,
  })
}
