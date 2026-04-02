import React from 'react'
import { AlertTriangle, Globe, Zap, Eye } from 'lucide-react'
import type { ThreatSummary } from '../types/protest'

interface StatsBarProps {
  totalEvents: number
  threatSummary: ThreatSummary | null
  countriesCount: number
  isLive: boolean
  lastUpdated: string | null
}

const StatPill: React.FC<{
  icon: React.ReactNode
  label: string
  value: string | number
  color: string
}> = ({ icon, label, value, color }) => (
  <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0d1b2e]/80 border border-[#1e3a5f] rounded-lg">
    <span style={{ color }}>{icon}</span>
    <div className="flex flex-col leading-none">
      <span className="text-[9px] text-[#8ba3c0] uppercase tracking-wider">{label}</span>
      <span className="text-sm font-bold text-[#e8f0fe]">{value}</span>
    </div>
  </div>
)

export const StatsBar: React.FC<StatsBarProps> = ({
  totalEvents,
  threatSummary,
  countriesCount,
  isLive,
  lastUpdated,
}) => {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <StatPill
        icon={<Globe className="w-3.5 h-3.5" />}
        label="Events"
        value={totalEvents.toLocaleString()}
        color="#64d2ff"
      />
      <StatPill
        icon={<AlertTriangle className="w-3.5 h-3.5" />}
        label="Critical"
        value={threatSummary?.CRITICAL ?? 0}
        color="#ff2d55"
      />
      <StatPill
        icon={<Zap className="w-3.5 h-3.5" />}
        label="High"
        value={threatSummary?.HIGH ?? 0}
        color="#ff6b35"
      />
      <StatPill
        icon={<Eye className="w-3.5 h-3.5" />}
        label="Countries"
        value={countriesCount}
        color="#30d158"
      />
      <div className="flex items-center gap-1.5 ml-auto">
        <span
          className={`w-2 h-2 rounded-full ${isLive ? 'bg-red-500 animate-pulse' : 'bg-gray-500'}`}
        />
        <span className={`text-xs font-medium ${isLive ? 'text-red-400' : 'text-gray-400'}`}>
          {isLive ? 'LIVE' : 'OFFLINE'}
        </span>
        {lastUpdated && (
          <span className="text-[#8ba3c0] text-[10px] ml-2">
            Updated {new Date(lastUpdated).toLocaleTimeString()}
          </span>
        )}
      </div>
    </div>
  )
}

export default StatsBar
