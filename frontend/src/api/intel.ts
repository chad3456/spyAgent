import axios from 'axios'
import type { IntelStatusResponse, TeamBriefResponse } from '../types/intel'

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api'

const api = axios.create({
  baseURL: API_BASE,
  // The team brief chains 8 Claude calls (1 Opus + 7 Haiku); give it room.
  timeout: 120_000,
})

export async function fetchIntelStatus(): Promise<IntelStatusResponse> {
  const { data } = await api.get<IntelStatusResponse>('/intel/status')
  return data
}

export async function fetchTeamBrief(): Promise<TeamBriefResponse> {
  const { data } = await api.get<TeamBriefResponse>('/intel/team-brief')
  return data
}
