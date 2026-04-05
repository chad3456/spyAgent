import React from 'react'
import { X, ExternalLink } from 'lucide-react'
import type { GlobePoint } from '../types/osint'

interface GlobePointModalProps {
  point: GlobePoint
  onClose: () => void
}

const LAYER_LABELS: Record<string, string> = {
  flights: '✈ Civil Aircraft',
  military_flights: '🛩 Military Aircraft',
  vessels: '🚢 Vessel',
  earthquakes: '🌋 Earthquake',
  ddos: '⚡ DDoS Attack',
  satellites: '🛰 Satellite',
  conflicts: '🔥 Conflict Event',
  health: '🏥 Health Alert',
  datacenters: '🖥 Data Infrastructure',
  social_feeds: '📡 Social Feed',
  news_intel: '📰 News Intel',
}

function renderData(data: unknown): React.ReactNode {
  if (!data || typeof data !== 'object') return null
  const obj = data as Record<string, unknown>
  const skip = new Set(['id', 'data', 'layer'])
  return (
    <div className="space-y-1">
      {Object.entries(obj)
        .filter(([k, v]) => !skip.has(k) && v != null && v !== '' && v !== false)
        .slice(0, 12)
        .map(([k, v]) => (
          <div key={k} className="flex gap-2 text-xs">
            <span className="text-[#8ba3c0] capitalize min-w-[90px] flex-shrink-0">
              {k.replace(/_/g, ' ')}
            </span>
            <span className="text-[#e8f0fe] break-all">
              {typeof v === 'boolean'
                ? v ? 'Yes' : 'No'
                : typeof v === 'number'
                ? v.toLocaleString()
                : String(v).slice(0, 100)}
            </span>
          </div>
        ))}
    </div>
  )
}

export const GlobePointModal: React.FC<GlobePointModalProps> = ({ point, onClose }) => {
  const layerLabel = LAYER_LABELS[point.layer] ?? point.layer
  const data = point.data as Record<string, unknown> | null
  const url = data?.url as string | undefined

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-[#0d1b2e] border border-[#1e3a5f] rounded-xl shadow-2xl w-full max-w-sm overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between px-4 py-3 bg-[#1e3a5f]/30 border-b border-[#1e3a5f]">
          <div>
            <div className="text-[#64d2ff] text-[10px] font-bold uppercase tracking-wider mb-0.5">
              {layerLabel}
            </div>
            <div className="text-[#e8f0fe] text-sm font-semibold leading-tight">
              {point.label.split('\n')[0]}
            </div>
          </div>
          <button onClick={onClose} className="text-[#8ba3c0] hover:text-[#e8f0fe] ml-3 flex-shrink-0">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="px-4 py-3 max-h-72 overflow-y-auto">
          <div className="text-[#8ba3c0] text-[11px] mb-3">
            📍 {point.lat.toFixed(4)}, {point.lng.toFixed(4)}
          </div>
          {renderData(point.data)}
        </div>

        {/* Footer */}
        {url && (
          <div className="px-4 py-2 border-t border-[#1e3a5f]">
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-[#64d2ff] text-xs hover:text-[#e8f0fe] transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              View source
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
