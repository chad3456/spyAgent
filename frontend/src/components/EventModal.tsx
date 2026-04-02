import React from 'react'
import { X, ExternalLink, MapPin, Clock, Database, AlertTriangle } from 'lucide-react'
import { format, parseISO, isValid } from 'date-fns'
import type { ProtestEvent, HAPIEvent } from '../types/protest'
import { ThreatBadge } from './ThreatBadge'

type AnyEvent = ProtestEvent | HAPIEvent

interface EventModalProps {
  event: AnyEvent
  onClose: () => void
}

function isProtestEvent(e: AnyEvent): e is ProtestEvent {
  return 'url' in e
}

function safeDate(str: string): string {
  try {
    const d = parseISO(str)
    if (isValid(d)) return format(d, 'dd MMM yyyy HH:mm z')
  } catch {}
  return str
}

export const EventModal: React.FC<EventModalProps> = ({ event, onClose }) => {
  const isProtest = isProtestEvent(event)

  return (
    <div
      className="fixed inset-0 z-[2000] flex items-center justify-center p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-lg bg-[#0d1b2e] border border-[#1e3a5f] rounded-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-start justify-between p-4 border-b border-[#1e3a5f]">
          <div className="flex-1 pr-3">
            <div className="flex items-center gap-2 mb-1.5">
              <ThreatBadge level={event.threatLevel} size="sm" />
              <span className="text-[10px] text-[#8ba3c0] uppercase tracking-wider font-semibold">
                {event.dataSource}
              </span>
            </div>
            <h2 className="text-[#e8f0fe] font-semibold text-sm leading-snug">
              {isProtest ? event.title : `${event.eventType} — ${event.country}`}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="flex-shrink-0 p-1.5 rounded-lg text-[#8ba3c0] hover:text-[#e8f0fe] hover:bg-[#1e3a5f] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Image */}
        {isProtest && event.image && (
          <div className="w-full h-40 overflow-hidden bg-[#0a0f1e]">
            <img
              src={event.image}
              alt={event.title}
              className="w-full h-full object-cover opacity-80"
              onError={(e) => {
                ;(e.target as HTMLImageElement).style.display = 'none'
              }}
            />
          </div>
        )}

        {/* Body */}
        <div className="p-4 space-y-3">
          {/* Location row */}
          <div className="flex items-center gap-2 text-[#8ba3c0] text-xs">
            <MapPin className="w-3.5 h-3.5 flex-shrink-0 text-[#64d2ff]" />
            <span>
              {[
                isProtest ? event.country : event.country,
                isProtest ? undefined : (event as HAPIEvent).admin1,
              ]
                .filter(Boolean)
                .join(' › ')}
            </span>
            <span className="ml-auto font-mono text-[10px]">
              {event.lat.toFixed(4)}, {event.lon.toFixed(4)}
            </span>
          </div>

          {/* Time row */}
          <div className="flex items-center gap-2 text-[#8ba3c0] text-xs">
            <Clock className="w-3.5 h-3.5 flex-shrink-0 text-[#64d2ff]" />
            <span>
              {isProtest ? safeDate(event.publishedAt) : safeDate((event as HAPIEvent).date)}
            </span>
          </div>

          {/* Data source */}
          <div className="flex items-center gap-2 text-[#8ba3c0] text-xs">
            <Database className="w-3.5 h-3.5 flex-shrink-0 text-[#64d2ff]" />
            <span>Source: {event.dataSource}</span>
            {isProtest && (
              <span className="text-[#8ba3c0]">
                via <span className="text-[#e8f0fe]">{event.source}</span>
              </span>
            )}
          </div>

          {/* HAPI-specific stats */}
          {!isProtest && (
            <div className="grid grid-cols-2 gap-2 mt-2">
              <div className="bg-[#0a0f1e] rounded-lg p-2 border border-[#1e3a5f]">
                <div className="text-[10px] text-[#8ba3c0] uppercase mb-0.5">Events</div>
                <div className="text-[#e8f0fe] font-bold">{(event as HAPIEvent).eventCount}</div>
              </div>
              <div className="bg-[#0a0f1e] rounded-lg p-2 border border-[#1e3a5f]">
                <div className="text-[10px] text-[#8ba3c0] uppercase mb-0.5">Fatalities</div>
                <div
                  className="font-bold"
                  style={{ color: (event as HAPIEvent).fatalities > 0 ? '#ff2d55' : '#30d158' }}
                >
                  {(event as HAPIEvent).fatalities}
                </div>
              </div>
            </div>
          )}

          {/* GDELT notes */}
          {isProtest && event.notes && (
            <p className="text-[#8ba3c0] text-xs leading-relaxed border-t border-[#1e3a5f] pt-2">
              {event.notes}
            </p>
          )}

          {/* Fatalities warning */}
          {!isProtest && (event as HAPIEvent).fatalities > 0 && (
            <div className="flex items-center gap-2 p-2 bg-red-500/10 border border-red-500/30 rounded-lg">
              <AlertTriangle className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
              <span className="text-red-300 text-xs">
                {(event as HAPIEvent).fatalities} reported fatalities
              </span>
            </div>
          )}
        </div>

        {/* Footer */}
        {isProtest && event.url && (
          <div className="px-4 pb-4">
            <a
              href={event.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 w-full py-2 bg-[#1e3a5f] hover:bg-[#2a4a7f] border border-[#2a5a8f] rounded-lg text-[#64d2ff] text-xs font-medium transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Read Full Article
            </a>
          </div>
        )}
      </div>
    </div>
  )
}

export default EventModal
