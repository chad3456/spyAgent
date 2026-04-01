import axios from 'axios'
import type { EconomicData, AIInfraData, InfrastructureData, DefenseData } from '../types'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error(`API Error ${error.response.status}:`, error.response.data)
    } else if (error.request) {
      console.error('Network Error: No response received', error.request)
    } else {
      console.error('Request setup error:', error.message)
    }
    return Promise.reject(error)
  }
)

export const fetchEconomicData = async (): Promise<EconomicData> => {
  const response = await apiClient.get<EconomicData>('/economic')
  return response.data
}

export const fetchAIInfraData = async (): Promise<AIInfraData> => {
  const response = await apiClient.get<AIInfraData>('/ai-infra')
  return response.data
}

export const fetchInfrastructureData = async (): Promise<InfrastructureData> => {
  const response = await apiClient.get<InfrastructureData>('/infrastructure')
  return response.data
}

export const fetchDefenseData = async (): Promise<DefenseData> => {
  const response = await apiClient.get<DefenseData>('/defense')
  return response.data
}

export default apiClient
