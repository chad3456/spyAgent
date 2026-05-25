import { useQuery } from '@tanstack/react-query'
import { fetchIntelStatus, fetchTeamBrief } from '../api/intel'
import type { IntelStatusResponse, TeamBriefResponse } from '../types/intel'

export function useIntelStatus() {
  return useQuery<IntelStatusResponse>({
    queryKey: ['intel_status'],
    queryFn: fetchIntelStatus,
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: 1,
  })
}

export function useTeamBrief(enabled: boolean) {
  return useQuery<TeamBriefResponse>({
    queryKey: ['team_brief'],
    queryFn: fetchTeamBrief,
    enabled,
    // Underlying OSINT feeds update at ~1-5 min cadence; refresh every 2 min.
    // The local heuristic team runs in 1-3 s; the Claude team caches 5 min server-side.
    staleTime: 120_000,
    refetchInterval: enabled ? 120_000 : false,
    retry: 0,
  })
}
