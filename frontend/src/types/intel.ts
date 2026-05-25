// Types for the Claude analyst team API surface.

export interface AnalystUsage {
  inputTokens: number
  outputTokens: number
  cacheReadInputTokens?: number
  cacheCreationInputTokens?: number
}

export interface AnalystEnvelope<T> {
  analyst: string
  model: string
  stopReason?: string
  usage?: AnalystUsage
  analysis: T | null
  disabled?: boolean
  reason?: string
  error?: string
}

export interface ThreatItem {
  id: string
  title: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  region: string
  summary: string
  confidence: number
  supportingSignals: string[]
}

export interface ThreatAnalysis {
  headline: string
  dataQuality: 'RICH' | 'ADEQUATE' | 'SPARSE'
  threats: ThreatItem[]
}

export interface CorrelationItem {
  id: string
  title: string
  feeds: string[]
  region: string
  summary: string
  strength: number
  implication: string
}

export interface CorrelationAnalysis {
  headline: string
  correlations: CorrelationItem[]
}

export interface RegionalAnalysis {
  country: string
  headline: string
  ownActivity: string[]
  threatsAgainst: string[]
  internalSignals: string[]
  escalationRisk: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'BASELINE'
  keyAssetsObserved: string[]
}

export interface BriefingThreat {
  title: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  rationale: string
}

export interface BriefingRegionalSnapshot {
  country: string
  posture: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'BASELINE'
  oneLine: string
}

export interface BriefingCorrelation {
  title: string
  feeds: string[]
  implication: string
}

export interface BriefingAnalysis {
  bottomLine: string
  topThreats: BriefingThreat[]
  regionalSnapshots: BriefingRegionalSnapshot[]
  keyCorrelations: BriefingCorrelation[]
  watchItems: string[]
  confidence: 'LOW' | 'MEDIUM' | 'HIGH'
}

export interface TeamBriefResponse {
  briefing: AnalystEnvelope<BriefingAnalysis>
  threats: AnalystEnvelope<ThreatAnalysis>
  correlations: AnalystEnvelope<CorrelationAnalysis>
  regional: Record<string, AnalystEnvelope<RegionalAnalysis>>
  teamUsage?: {
    totalInputTokens: number
    totalOutputTokens: number
    totalCacheReadInputTokens: number
    analystCount: number
  }
  generatedAt: string
  disabled?: boolean
  reason?: string
}

export interface IntelStatusResponse {
  claudeAvailable: boolean
  countries: string[]
  analysts: string[]
  briefingModel: string
  analystModel: string
  timestamp: string
}
