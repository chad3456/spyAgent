import React, { useMemo } from 'react'
import { MapPin, ExternalLink, ChevronRight } from 'lucide-react'
import { formatDistanceToNow, parseISO, isValid } from 'date-fns'
import clsx from 'clsx'
import type { ProtestEvent, HAPIEvent, FilterState } from '../types/protest'
import { THREAT_CONFIG } from '../types/protest'
import { ThreatBadge } from './ThreatBadge'

type AnyEvent = ProtestEvent | HAPIEvent

function isProtestEvent(e: AnyEvent): e is ProtestEvent {
  return 'url' in e
}

function relativeTime(str: string): string {
  try {
    const d = parseISO(str)
    if (isValid(d)) return formatDistanceToNow(d, { addSuffix: true })
  } catch {}
  return str
}

interface EventSidebarProps {
  protests: ProtestEvent[]
  hapiEvents: HAPIEvent[]
  filters: FilterState
  selectedEventId: string | null
  onSelectEvent: (e: AnyEvent) => void
  loading: boolean
}

export const EventSidebar: React.FC<EventSidebarProps> = ({
  protests,
  hapiEvents,
  filters,
  selectedEventId,
  onSelectEvent,
  loading,
}) => {
  const filteredEvents = useMemo<AnyEvent[]>(() => {
    const q = filters.searchQuery.toLowerCase()
    const results: AnyEvent[] = []

    if (filters.showGDELT) {
      protests
        .filter((e) => filters.threatLevels.includes(e.threatLevel))
        .filter(
          (e) =>
            !q ||
            e.title.toLowerCase().includes(q) ||
            e.country.toLowerCase().includes(q)
        )
        .forEach((e) => results.push(e))
    }

    if (filters.showHAPI) {
      hapiEvents
        .filter((e) => filters.threatLevels.includes(e.threatLevel))
        .filter(
          (e) =>
            !q ||
            e.country.toLowerCase().includes(q) ||
            e.eventType.toLowerCase().includes(q)
        )
        .forEach((e) => results.push(e))
    }

    // Sort by threat level severity then date
    const threatOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, INFO: 4 }
    results.sort((a, b) => {
      const ta = threatOrder[a.threatLevel] ?? 5
      const tb = threatOrder[b.threatLevel] ?? 5
      if (ta !== tb) return ta - tb
      const da = isProtestEvent(a) ? a.publishedAt : a.date
      const db = isProtestEvent(b) ? b.publishedAt : b.date
      return db.localeCompare(da)
    })

    return results.slice(0, 200)
  }, [protests, hapiEvents, filters])

  if (loading) {
    return (
      <div className="flex flex-col gap-2 p-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-20 bg-[#1e3a5f]/30 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  if (!filteredEvents.length) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-[#8ba3c0] text-sm gap-2">
        <MapPin className="w-8 h-8 opacity-30" />
        <span>No events match filters</span>
      </div>
    )
  }

  return (
    <div className="overflow-y-auto flex-1 divide-y divide-[#1e3a5f]/40">
      {filteredEvents.map((event) => {
        const isSelected = event.id === selectedEventId
        const cfg = THREAT_CONFIG[event.threatLevel]
        const isProtest = isProtestEvent(event)
        const title = isProtest ? event.title : `${event.eventType} — ${event.country}`
        const location = isProtest
          ? event.country
          : [event.country, event.admin1].filter(Boolean).join(', ')
        const time = isProtest ? event.publishedAt : event.date
        const src = event.dataSource

        return (
          <div
            key={event.id}
            onClick={() => onSelectEvent(event)}
            className={clsx(
              'flex items-start gap-2.5 p-3 cursor-pointer transition-colors hover:bg-[#1e3a5f]/30 group',
              isSelected && 'bg-[#1e3a5f]/50 border-l-2'
            )}
            style={isSelected ? { borderLeftColor: cfg.color } : {}}
          >
            {/* Threat color strip */}
            <div
              className="w-1 flex-shrink-0 rounded-full self-stretch min-h-[40px]"
              style={{ backgroundColor: cfg.color, opacity: 0.8 }}
            />

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5 mb-1">
                <ThreatBadge level={event.threatLevel} size="sm" />
                <span className="text-[9px] text-[#8ba3c0] uppercase tracking-wider truncate">
                  {src}
                </span>
              </div>
              <p className="text-[#e8f0fe] text-xs leading-snug line-clamp-2 mb-1">{title}</p>
              <div className="flex items-center gap-1.5 text-[#8ba3c0] text-[10px]">
                <MapPin className="w-3 h-3 flex-shrink-0" />
                <span className="truncate">{location}</span>
                <span className="ml-auto flex-shrink-0 whitespace-nowrap">
                  {relativeTime(time)}
                </span>
              </div>
              {!isProtest && (
                <div className="flex items-center gap-3 mt-1 text-[10px]">
                  <span className="text-[#8ba3c0]">
                    Events: <span className="text-[#e8f0fe]">{event.eventCount}</span>
                  </span>
                  {event.fatalities > 0 && (
                    <span className="text-red-400">
                      Fatalities: {event.fatalities}
                    </span>
                  )}
                </div>
              )}
            </div>

            <div className="flex flex-col items-end gap-1 flex-shrink-0">
              {isProtest && event.url && (
                <a
                  href={event.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="text-[#64d2ff] hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
              <ChevronRight className="w-3.5 h-3.5 text-[#1e3a5f] group-hover:text-[#8ba3c0] transition-colors" />
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default EventSidebar
