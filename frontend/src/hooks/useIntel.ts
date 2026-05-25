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
    // Backend caches per analyst for 5 min; refresh the dashboard view every 5 min too.
    staleTime: 5 * 60_000,
    refetchInterval: enabled ? 5 * 60_000 : false,
    retry: 0,
  })
}
