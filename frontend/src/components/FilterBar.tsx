import React from 'react'
import { Search, SlidersHorizontal } from 'lucide-react'
import clsx from 'clsx'
import type { FilterState, ThreatLevel } from '../types/protest'
import { THREAT_CONFIG } from '../types/protest'

interface FilterBarProps {
  filters: FilterState
  onChange: (f: FilterState) => void
}

const THREAT_LEVELS: ThreatLevel[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
const TIMESPANS: FilterState['timespan'][] = ['6h', '24h', '48h', '7d']

export const FilterBar: React.FC<FilterBarProps> = ({ filters, onChange }) => {
  const toggleThreat = (level: ThreatLevel) => {
    const next = filters.threatLevels.includes(level)
      ? filters.threatLevels.filter((l) => l !== level)
      : [...filters.threatLevels, level]
    onChange({ ...filters, threatLevels: next })
  }

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#8ba3c0]" />
        <input
          type="text"
          placeholder="Search events…"
          value={filters.searchQuery}
          onChange={(e) => onChange({ ...filters, searchQuery: e.target.value })}
          className="pl-8 pr-3 py-1.5 bg-[#0d1b2e] border border-[#1e3a5f] rounded-lg text-[#e8f0fe] text-xs placeholder-[#8ba3c0] focus:outline-none focus:border-[#64d2ff] w-44"
        />
      </div>

      {/* Threat level filters */}
      <div className="flex items-center gap-1">
        <SlidersHorizontal className="w-3.5 h-3.5 text-[#8ba3c0] mr-0.5" />
        {THREAT_LEVELS.map((level) => {
          const cfg = THREAT_CONFIG[level]
          const active = filters.threatLevels.includes(level)
          return (
            <button
              key={level}
              onClick={() => toggleThreat(level)}
              className={clsx(
                'text-[9px] font-bold px-2 py-1 rounded uppercase tracking-wider border transition-all',
                active ? 'opacity-100' : 'opacity-30 hover:opacity-60'
              )}
              style={{
                color: cfg.color,
                borderColor: cfg.border,
                backgroundColor: active ? cfg.bg : 'transparent',
              }}
            >
              {level}
            </button>
          )
        })}
      </div>

      {/* Timespan */}
      <div className="flex items-center gap-1 ml-auto">
        {TIMESPANS.map((ts) => (
          <button
            key={ts}
            onClick={() => onChange({ ...filters, timespan: ts })}
            className={clsx(
              'text-[10px] px-2 py-1 rounded border transition-all',
              filters.timespan === ts
                ? 'border-[#64d2ff] text-[#64d2ff] bg-[#64d2ff]/10'
                : 'border-[#1e3a5f] text-[#8ba3c0] hover:border-[#64d2ff]/50'
            )}
          >
            {ts}
          </button>
        ))}
      </div>

      {/* Source toggles */}
      <div className="flex items-center gap-1.5">
        {(['GDELT', 'HAPI/OCHA'] as const).map((src) => {
          const key = src === 'GDELT' ? 'showGDELT' : 'showHAPI'
          const on = filters[key]
          return (
            <button
              key={src}
              onClick={() => onChange({ ...filters, [key]: !on })}
              className={clsx(
                'text-[9px] font-semibold px-2 py-1 rounded border transition-all uppercase tracking-wider',
                on
                  ? 'border-[#1e3a5f] text-[#64d2ff] bg-[#64d2ff]/10'
                  : 'border-[#1e3a5f] text-[#8ba3c0] opacity-40 hover:opacity-70'
              )}
            >
              {src}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default FilterBar
