import React, { useState } from 'react'
import { Layers, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react'
import clsx from 'clsx'
import { LAYER_CONFIGS, type LayerKey } from '../types/osint'

interface LayerControlProps {
  activeLayers: Set<LayerKey>
  onToggleLayer: (key: LayerKey) => void
  loadingLayers?: Set<LayerKey>
  className?: string
}

export const LayerControl: React.FC<LayerControlProps> = ({
  activeLayers,
  onToggleLayer,
  loadingLayers = new Set(),
  className,
}) => {
  const [expanded, setExpanded] = useState(true)

  return (
    <div
      className={clsx(
        'bg-[#0d1b2e]/95 backdrop-blur-sm border border-[#1e3a5f] rounded-xl overflow-hidden shadow-2xl',
        className
      )}
      style={{ minWidth: 220 }}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center gap-2 px-3 py-2.5 bg-[#1e3a5f]/40 hover:bg-[#1e3a5f]/60 transition-colors"
      >
        <Layers className="w-4 h-4 text-[#64d2ff] flex-shrink-0" />
        <span className="text-[#e8f0fe] text-xs font-bold uppercase tracking-wider flex-1 text-left">
          OSINT Layers
        </span>
        <span className="text-[9px] bg-[#1e3a5f] text-[#64d2ff] px-1.5 py-0.5 rounded-full font-bold">
          {activeLayers.size}
        </span>
        {expanded ? (
          <ChevronUp className="w-3.5 h-3.5 text-[#8ba3c0]" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-[#8ba3c0]" />
        )}
      </button>

      {/* Layer list */}
      {expanded && (
        <div className="divide-y divide-[#1e3a5f]/50">
          {LAYER_CONFIGS.map((layer) => {
            const active = activeLayers.has(layer.key)
            const loading = loadingLayers.has(layer.key)
            return (
              <button
                key={layer.key}
                onClick={() => onToggleLayer(layer.key)}
                className={clsx(
                  'w-full flex items-center gap-2.5 px-3 py-2 text-left transition-all group',
                  active ? 'bg-[#1e3a5f]/30' : 'hover:bg-[#1e3a5f]/15'
                )}
              >
                {/* Dot indicator */}
                <div
                  className={clsx(
                    'w-2 h-2 rounded-full flex-shrink-0 transition-all',
                    active ? 'animate-pulse' : 'opacity-30'
                  )}
                  style={{ backgroundColor: layer.color }}
                />

                {/* Icon + Label */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm leading-none">{layer.icon}</span>
                    <span
                      className={clsx(
                        'text-xs font-medium truncate transition-colors',
                        active ? 'text-[#e8f0fe]' : 'text-[#8ba3c0] group-hover:text-[#e8f0fe]'
                      )}
                    >
                      {layer.label}
                    </span>
                    {loading && (
                      <RefreshCw
                        className="w-2.5 h-2.5 text-[#64d2ff] animate-spin flex-shrink-0"
                      />
                    )}
                  </div>
                  <p className="text-[9px] text-[#8ba3c0]/70 mt-0.5 truncate leading-tight">
                    {layer.description}
                  </p>
                </div>

                {/* Toggle indicator */}
                <div
                  className={clsx(
                    'w-8 h-4 rounded-full flex-shrink-0 transition-all relative',
                    active ? 'bg-[#1e3a5f]' : 'bg-[#0a0f1e]'
                  )}
                  style={{ border: `1px solid ${active ? layer.color : '#1e3a5f'}` }}
                >
                  <div
                    className="absolute top-0.5 w-3 h-3 rounded-full transition-all"
                    style={{
                      backgroundColor: active ? layer.color : '#4a6080',
                      left: active ? 'calc(100% - 14px)' : '1px',
                    }}
                  />
                </div>
              </button>
            )
          })}
        </div>
      )}

      {/* Footer note */}
      {expanded && (
        <div className="px-3 py-1.5 border-t border-[#1e3a5f]/50">
          <p className="text-[9px] text-[#8ba3c0]/60 text-center">
            Toggle layers to load live data
          </p>
        </div>
      )}
    </div>
  )
}
