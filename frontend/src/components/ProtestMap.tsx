import React, { useEffect, useRef, useMemo } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { ProtestEvent, HAPIEvent, FilterState } from '../types/protest'
import { THREAT_CONFIG } from '../types/protest'

// Fix default icon path broken by bundlers
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

type AnyEvent = ProtestEvent | HAPIEvent

function isProtestEvent(e: AnyEvent): e is ProtestEvent {
  return 'url' in e
}

function createThreatIcon(level: AnyEvent['threatLevel'], isHAPI = false): L.DivIcon {
  const cfg = THREAT_CONFIG[level]
  const size = level === 'CRITICAL' ? 14 : level === 'HIGH' ? 12 : 10
  const pulse = level === 'CRITICAL' || level === 'HIGH'

  return L.divIcon({
    html: `
      <div style="position:relative;width:${size + 6}px;height:${size + 6}px;display:flex;align-items:center;justify-content:center;">
        ${
          pulse
            ? `<div style="position:absolute;inset:0;border-radius:50%;background:${cfg.color};opacity:0.3;animation:ping 1.5s cubic-bezier(0,0,0.2,1) infinite;"></div>`
            : ''
        }
        <div style="
          width:${size}px;
          height:${size}px;
          background:${cfg.color};
          border:2px solid ${cfg.color === '#ff2d55' ? '#fff' : 'rgba(255,255,255,0.6)'};
          border-radius:${isHAPI ? '3px' : '50%'};
          box-shadow:0 0 6px ${cfg.color}99;
        "></div>
      </div>
    `,
    className: '',
    iconSize: [size + 6, size + 6],
    iconAnchor: [(size + 6) / 2, (size + 6) / 2],
    popupAnchor: [0, -(size + 6) / 2],
  })
}

function buildPopupHtml(event: AnyEvent): string {
  const cfg = THREAT_CONFIG[event.threatLevel]
  const isProtest = isProtestEvent(event)
  const title = isProtest ? event.title : `${event.eventType} — ${event.country}`
  const location = isProtest
    ? event.country
    : [event.country, (event as HAPIEvent).admin1].filter(Boolean).join(', ')
  const time = isProtest ? event.publishedAt : (event as HAPIEvent).date
  const displayTime = time ? new Date(time).toLocaleDateString() : ''

  const imageHtml =
    isProtest && event.image
      ? `<img src="${event.image}" alt="" style="width:100%;height:70px;object-fit:cover;border-radius:4px 4px 0 0;margin:-8px -8px 8px -8px;width:calc(100% + 16px);" onerror="this.style.display='none'" />`
      : ''

  const statsHtml = !isProtest
    ? `<div style="display:flex;gap:8px;margin-top:6px;">
        <span style="font-size:10px;color:#8ba3c0;">Events: <b style="color:#e8f0fe">${(event as HAPIEvent).eventCount}</b></span>
        <span style="font-size:10px;color:${(event as HAPIEvent).fatalities > 0 ? '#ff2d55' : '#8ba3c0'};">
          Fatalities: <b>${(event as HAPIEvent).fatalities}</b>
        </span>
      </div>`
    : ''

  const linkHtml =
    isProtest && event.url
      ? `<a href="${event.url}" target="_blank" rel="noopener noreferrer"
          style="display:block;margin-top:8px;padding:4px 8px;background:#1e3a5f;border-radius:4px;color:#64d2ff;font-size:10px;text-align:center;text-decoration:none;">
          Read Article ↗
        </a>`
      : ''

  return `
    <div style="font-family:system-ui,sans-serif;max-width:220px;padding:8px;background:#0d1b2e;color:#e8f0fe;border-radius:6px;">
      ${imageHtml}
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
        <span style="
          display:inline-flex;align-items:center;gap:4px;
          padding:2px 6px;border-radius:4px;
          background:${cfg.bg};border:1px solid ${cfg.border};
          color:${cfg.color};font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;
        ">
          <span style="width:6px;height:6px;border-radius:50%;background:${cfg.color};"></span>
          ${cfg.label}
        </span>
        <span style="font-size:9px;color:#8ba3c0;text-transform:uppercase;">${event.dataSource}</span>
      </div>
      <p style="font-size:11px;font-weight:600;line-height:1.4;margin:0 0 4px;">${title}</p>
      <p style="font-size:10px;color:#8ba3c0;margin:0;">${location}</p>
      ${displayTime ? `<p style="font-size:10px;color:#8ba3c0;margin:2px 0 0;">${displayTime}</p>` : ''}
      ${statsHtml}
      ${linkHtml}
    </div>
  `
}

interface ProtestMapProps {
  protests: ProtestEvent[]
  hapiEvents: HAPIEvent[]
  filters: FilterState
  selectedEventId: string | null
  onSelectEvent: (e: AnyEvent) => void
}

export const ProtestMap: React.FC<ProtestMapProps> = ({
  protests,
  hapiEvents,
  filters,
  selectedEventId,
  onSelectEvent,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const layersRef = useRef<L.LayerGroup | null>(null)
  const markersRef = useRef<Map<string, L.Marker>>(new Map())

  // Init map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const map = L.map(containerRef.current, {
      center: [20, 10],
      zoom: 2,
      minZoom: 2,
      maxZoom: 16,
      zoomControl: false,
    })

    // Dark tile layer — CartoDB Dark Matter
    L.tileLayer(
      'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      {
        attribution:
          '&copy; <a href="https://carto.com/">CARTO</a> | &copy; <a href="https://osm.org/copyright">OpenStreetMap</a>',
        subdomains: 'abcd',
        maxZoom: 20,
      }
    ).addTo(map)

    // Zoom control bottom-right
    L.control.zoom({ position: 'bottomright' }).addTo(map)

    // Layer group for markers
    const layerGroup = L.layerGroup().addTo(map)

    // Inject ping keyframe CSS once
    const style = document.createElement('style')
    style.textContent = `
      @keyframes ping {
        75%, 100% { transform: scale(2.5); opacity: 0; }
      }
    `
    document.head.appendChild(style)

    mapRef.current = map
    layersRef.current = layerGroup

    return () => {
      map.remove()
      mapRef.current = null
      layersRef.current = null
    }
  }, [])

  // All visible events (filtered)
  const allEvents = useMemo<AnyEvent[]>(() => {
    const q = filters.searchQuery.toLowerCase()
    const result: AnyEvent[] = []

    if (filters.showGDELT) {
      protests
        .filter((e) => filters.threatLevels.includes(e.threatLevel))
        .filter((e) => !q || e.title.toLowerCase().includes(q) || e.country.toLowerCase().includes(q))
        .forEach((e) => result.push(e))
    }

    if (filters.showHAPI) {
      hapiEvents
        .filter((e) => filters.threatLevels.includes(e.threatLevel))
        .filter((e) => !q || e.country.toLowerCase().includes(q))
        .forEach((e) => result.push(e))
    }

    return result
  }, [protests, hapiEvents, filters])

  // Rebuild markers when events change
  useEffect(() => {
    const layer = layersRef.current
    if (!layer) return

    layer.clearLayers()
    markersRef.current.clear()

    for (const event of allEvents) {
      if (!isFinite(event.lat) || !isFinite(event.lon)) continue

      const isHAPI = event.dataSource === 'HAPI/OCHA'
      const icon = createThreatIcon(event.threatLevel, isHAPI)

      const marker = L.marker([event.lat, event.lon], { icon })

      const popup = L.popup({
        className: 'protest-popup',
        maxWidth: 240,
        minWidth: 180,
      }).setContent(buildPopupHtml(event))

      marker.bindPopup(popup)
      marker.on('click', () => onSelectEvent(event))

      layer.addLayer(marker)
      markersRef.current.set(event.id, marker)
    }
  }, [allEvents, onSelectEvent])

  // Pan to selected event
  useEffect(() => {
    if (!selectedEventId || !mapRef.current) return
    const marker = markersRef.current.get(selectedEventId)
    if (marker) {
      mapRef.current.flyTo(marker.getLatLng(), Math.max(mapRef.current.getZoom(), 5), {
        animate: true,
        duration: 0.8,
      })
      marker.openPopup()
    }
  }, [selectedEventId])

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full" />

      {/* Map legend */}
      <div className="absolute bottom-8 left-3 z-[1000] bg-[#0d1b2e]/90 border border-[#1e3a5f] rounded-lg p-2.5 backdrop-blur-sm">
        <p className="text-[9px] text-[#8ba3c0] uppercase tracking-wider mb-1.5 font-semibold">
          Threat Level
        </p>
        {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((level) => {
          const cfg = THREAT_CONFIG[level]
          return (
            <div key={level} className="flex items-center gap-2 mb-1">
              <span
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: cfg.color }}
              />
              <span className="text-[10px]" style={{ color: cfg.color }}>
                {cfg.label}
              </span>
            </div>
          )
        })}
        <div className="mt-1.5 pt-1.5 border-t border-[#1e3a5f] space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#64d2ff] flex-shrink-0" />
            <span className="text-[10px] text-[#8ba3c0]">GDELT (circle)</span>
          </div>
          <div className="flex items-center gap-2">
            <span
              className="w-2.5 h-2.5 flex-shrink-0"
              style={{ background: '#64d2ff', borderRadius: '2px' }}
            />
            <span className="text-[10px] text-[#8ba3c0]">HAPI (square)</span>
          </div>
        </div>
      </div>

      {/* Event count badge */}
      <div className="absolute top-3 left-3 z-[1000] bg-[#0d1b2e]/90 border border-[#1e3a5f] rounded-lg px-2.5 py-1.5 backdrop-blur-sm">
        <span className="text-[10px] text-[#8ba3c0]">
          Showing{' '}
          <span className="text-[#64d2ff] font-bold">{allEvents.length}</span> events
        </span>
      </div>
    </div>
  )
}

export default ProtestMap
