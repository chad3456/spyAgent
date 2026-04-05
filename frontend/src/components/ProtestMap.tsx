import React, { useEffect, useRef, useMemo } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { ProtestEvent, HAPIEvent, FilterState } from '../types/protest'
import { THREAT_CONFIG } from '../types/protest'
import type {
  Aircraft,
  MilitaryAircraft,
  Vessel,
  Earthquake,
  DDoSCountry,
  Satellite,
  HealthOutbreak,
  DatacenterFacility,
  LayerKey,
} from '../types/osint'

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

// ─── Icon factories ────────────────────────────────────────────────────────────

function createThreatIcon(level: AnyEvent['threatLevel'], isHAPI = false): L.DivIcon {
  const cfg = THREAT_CONFIG[level]
  const size = level === 'CRITICAL' ? 14 : level === 'HIGH' ? 12 : 10
  const pulse = level === 'CRITICAL' || level === 'HIGH'
  return L.divIcon({
    html: `
      <div style="position:relative;width:${size + 6}px;height:${size + 6}px;display:flex;align-items:center;justify-content:center;">
        ${pulse ? `<div style="position:absolute;inset:0;border-radius:50%;background:${cfg.color};opacity:0.3;animation:ping 1.5s cubic-bezier(0,0,0.2,1) infinite;"></div>` : ''}
        <div style="width:${size}px;height:${size}px;background:${cfg.color};border:2px solid rgba(255,255,255,0.6);border-radius:${isHAPI ? '3px' : '50%'};box-shadow:0 0 6px ${cfg.color}99;"></div>
      </div>`,
    className: '',
    iconSize: [size + 6, size + 6],
    iconAnchor: [(size + 6) / 2, (size + 6) / 2],
    popupAnchor: [0, -(size + 6) / 2],
  })
}

function createFlightIcon(heading: number, color = '#64d2ff', size = 14): L.DivIcon {
  return L.divIcon({
    html: `<div style="transform:rotate(${heading}deg);font-size:${size}px;line-height:1;color:${color};text-shadow:0 0 4px ${color}88;filter:drop-shadow(0 0 3px ${color});">✈</div>`,
    className: '',
    iconSize: [size + 4, size + 4],
    iconAnchor: [(size + 4) / 2, (size + 4) / 2],
    popupAnchor: [0, -(size + 4) / 2],
  })
}

function createDotIcon(color: string, size: number, emoji?: string): L.DivIcon {
  if (emoji) {
    return L.divIcon({
      html: `<div style="font-size:${size}px;line-height:1;text-shadow:0 0 4px ${color}88;filter:drop-shadow(0 0 3px ${color});">${emoji}</div>`,
      className: '',
      iconSize: [size + 4, size + 4],
      iconAnchor: [(size + 4) / 2, (size + 4) / 2],
      popupAnchor: [0, -(size + 4) / 2],
    })
  }
  return L.divIcon({
    html: `<div style="width:${size}px;height:${size}px;background:${color};border-radius:50%;border:1.5px solid rgba(255,255,255,0.5);box-shadow:0 0 5px ${color};"></div>`,
    className: '',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  })
}

function eqIcon(mag: number): L.DivIcon {
  const size = Math.max(10, Math.min(28, mag * 4))
  const color = mag >= 7 ? '#ff2d55' : mag >= 6 ? '#ff6b35' : mag >= 5 ? '#ffd60a' : '#30d158'
  return L.divIcon({
    html: `
      <div style="position:relative;width:${size + 6}px;height:${size + 6}px;display:flex;align-items:center;justify-content:center;">
        <div style="position:absolute;inset:0;border-radius:50%;background:${color};opacity:0.25;animation:ping 2s ease-in-out infinite;"></div>
        <div style="width:${size}px;height:${size}px;background:${color};border-radius:50%;border:1.5px solid rgba(255,255,255,0.5);box-shadow:0 0 8px ${color};display:flex;align-items:center;justify-content:center;">
          <span style="font-size:${Math.max(6, size - 6)}px;line-height:1;">🌋</span>
        </div>
      </div>`,
    className: '',
    iconSize: [size + 6, size + 6],
    iconAnchor: [(size + 6) / 2, (size + 6) / 2],
    popupAnchor: [0, -(size + 6) / 2],
  })
}

// ─── Popup builders ────────────────────────────────────────────────────────────

function buildPopupHtml(event: AnyEvent): string {
  const cfg = THREAT_CONFIG[event.threatLevel]
  const isProtest = isProtestEvent(event)
  const title = isProtest ? event.title : `${event.eventType} — ${event.country}`
  const location = isProtest
    ? event.country
    : [event.country, (event as HAPIEvent).admin1].filter(Boolean).join(', ')
  const time = isProtest ? event.publishedAt : (event as HAPIEvent).date
  const displayTime = time ? new Date(time).toLocaleDateString() : ''
  const imageHtml = isProtest && event.image
    ? `<img src="${event.image}" alt="" style="width:calc(100%+16px);height:70px;object-fit:cover;border-radius:4px 4px 0 0;margin:-8px -8px 8px -8px;" onerror="this.style.display='none'" />`
    : ''
  const statsHtml = !isProtest
    ? `<div style="display:flex;gap:8px;margin-top:6px;"><span style="font-size:10px;color:#8ba3c0;">Events: <b style="color:#e8f0fe">${(event as HAPIEvent).eventCount}</b></span><span style="font-size:10px;color:${(event as HAPIEvent).fatalities > 0 ? '#ff2d55' : '#8ba3c0'};">Fatalities: <b>${(event as HAPIEvent).fatalities}</b></span></div>`
    : ''
  const linkHtml = isProtest && event.url
    ? `<a href="${event.url}" target="_blank" rel="noopener noreferrer" style="display:block;margin-top:8px;padding:4px 8px;background:#1e3a5f;border-radius:4px;color:#64d2ff;font-size:10px;text-align:center;text-decoration:none;">Read Article ↗</a>`
    : ''
  return `<div style="font-family:system-ui,sans-serif;max-width:220px;padding:8px;background:#0d1b2e;color:#e8f0fe;border-radius:6px;">${imageHtml}<div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;"><span style="display:inline-flex;align-items:center;gap:4px;padding:2px 6px;border-radius:4px;background:${cfg.bg};border:1px solid ${cfg.border};color:${cfg.color};font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;"><span style="width:6px;height:6px;border-radius:50%;background:${cfg.color};"></span>${cfg.label}</span><span style="font-size:9px;color:#8ba3c0;text-transform:uppercase;">${event.dataSource}</span></div><p style="font-size:11px;font-weight:600;line-height:1.4;margin:0 0 4px;">${title}</p><p style="font-size:10px;color:#8ba3c0;margin:0;">${location}</p>${displayTime ? `<p style="font-size:10px;color:#8ba3c0;margin:2px 0 0;">${displayTime}</p>` : ''}${statsHtml}${linkHtml}</div>`
}

function flightPopup(a: Aircraft | MilitaryAircraft): string {
  const isMil = 'military' in a && (a as MilitaryAircraft).military
  const color = isMil ? '#ff2d55' : '#64d2ff'
  return `<div style="font-family:system-ui,sans-serif;padding:8px;background:#0d1b2e;color:#e8f0fe;border-radius:6px;min-width:160px;">
    <div style="font-size:9px;color:${color};font-weight:700;text-transform:uppercase;margin-bottom:4px;">${isMil ? '🛩 Military Aircraft' : '✈ Civil Aircraft'}</div>
    <div style="font-size:12px;font-weight:600;margin-bottom:4px;">${a.callsign || a.icao24}</div>
    <div style="font-size:10px;color:#8ba3c0;">Country: ${a.country}</div>
    <div style="font-size:10px;color:#8ba3c0;">Alt: ${a.altitude != null ? Math.round(a.altitude) + ' m' : 'N/A'}</div>
    <div style="font-size:10px;color:#8ba3c0;">Speed: ${a.velocity != null ? Math.round(a.velocity) + ' km/h' : 'N/A'}</div>
    <div style="font-size:10px;color:#8ba3c0;">Heading: ${a.heading != null ? Math.round(a.heading) + '°' : 'N/A'}</div>
    ${isMil && (a as MilitaryAircraft).nation ? `<div style="font-size:10px;color:#ff2d55;margin-top:2px;">Nation: ${(a as MilitaryAircraft).nation}</div>` : ''}
  </div>`
}

function vesselPopup(v: Vessel): string {
  return `<div style="font-family:system-ui,sans-serif;padding:8px;background:#0d1b2e;color:#e8f0fe;border-radius:6px;min-width:160px;">
    <div style="font-size:9px;color:#30d158;font-weight:700;text-transform:uppercase;margin-bottom:4px;">🚢 Vessel</div>
    <div style="font-size:12px;font-weight:600;margin-bottom:4px;">${v.name || v.mmsi}</div>
    <div style="font-size:10px;color:#8ba3c0;">Type: ${v.shipType || v.type || 'Unknown'}</div>
    <div style="font-size:10px;color:#8ba3c0;">Speed: ${v.speed != null ? v.speed + ' kts' : 'N/A'}</div>
    ${v.destination ? `<div style="font-size:10px;color:#8ba3c0;">Dest: ${v.destination}</div>` : ''}
    ${v.flag ? `<div style="font-size:10px;color:#8ba3c0;">Flag: ${v.flag}</div>` : ''}
  </div>`
}

function eqPopup(eq: Earthquake): string {
  const color = eq.severity === 'CRITICAL' ? '#ff2d55' : eq.severity === 'HIGH' ? '#ff6b35' : eq.severity === 'MEDIUM' ? '#ffd60a' : '#30d158'
  return `<div style="font-family:system-ui,sans-serif;padding:8px;background:#0d1b2e;color:#e8f0fe;border-radius:6px;min-width:180px;">
    <div style="font-size:9px;color:${color};font-weight:700;text-transform:uppercase;margin-bottom:4px;">🌋 Earthquake ${eq.severity}</div>
    <div style="font-size:14px;font-weight:700;margin-bottom:4px;color:${color};">M ${eq.magnitude?.toFixed(1)}</div>
    <div style="font-size:11px;font-weight:600;margin-bottom:4px;">${eq.place}</div>
    <div style="font-size:10px;color:#8ba3c0;">Depth: ${eq.depth} km</div>
    ${eq.tsunami ? '<div style="font-size:10px;color:#ff2d55;font-weight:700;margin-top:4px;">⚠ TSUNAMI WARNING</div>' : ''}
    ${eq.url ? `<a href="${eq.url}" target="_blank" rel="noopener noreferrer" style="display:block;margin-top:6px;padding:3px 8px;background:#1e3a5f;border-radius:4px;color:#64d2ff;font-size:10px;text-align:center;text-decoration:none;">USGS Details ↗</a>` : ''}
  </div>`
}

function genericPopup(emoji: string, _title: string, color: string, fields: [string, string | number | undefined][]): string {
  const rows = fields.filter(([, v]) => v != null && v !== '').map(([k, v]) =>
    `<div style="font-size:10px;color:#8ba3c0;">${k}: <span style="color:#e8f0fe">${v}</span></div>`
  ).join('')
  return `<div style="font-family:system-ui,sans-serif;padding:8px;background:#0d1b2e;color:#e8f0fe;border-radius:6px;min-width:160px;"><div style="font-size:9px;color:${color};font-weight:700;text-transform:uppercase;margin-bottom:4px;">${emoji}</div>${rows}</div>`
}

// ─── Component ────────────────────────────────────────────────────────────────

export interface OSINTLayerData {
  flights: Aircraft[]
  militaryFlights: MilitaryAircraft[]
  vessels: Vessel[]
  earthquakes: Earthquake[]
  ddos: DDoSCountry[]
  satellites: Satellite[]
  healthOutbreaks: HealthOutbreak[]
  datacenters: DatacenterFacility[]
  activeLayers: Set<LayerKey>
}

interface ProtestMapProps {
  protests: ProtestEvent[]
  hapiEvents: HAPIEvent[]
  filters: FilterState
  selectedEventId: string | null
  onSelectEvent: (e: AnyEvent) => void
  osint?: OSINTLayerData
}

export const ProtestMap: React.FC<ProtestMapProps> = ({
  protests,
  hapiEvents,
  filters,
  selectedEventId,
  onSelectEvent,
  osint,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const conflictLayerRef = useRef<L.LayerGroup | null>(null)
  const osintLayerRef = useRef<L.LayerGroup | null>(null)
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

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a> | &copy; <a href="https://osm.org/copyright">OpenStreetMap</a>',
      subdomains: 'abcd',
      maxZoom: 20,
    }).addTo(map)

    L.control.zoom({ position: 'bottomright' }).addTo(map)

    const conflictLayer = L.layerGroup().addTo(map)
    const osintLayer = L.layerGroup().addTo(map)

    // Inject keyframe CSS
    if (!document.getElementById('leaflet-anim-style')) {
      const style = document.createElement('style')
      style.id = 'leaflet-anim-style'
      style.textContent = `@keyframes ping{75%,100%{transform:scale(2.5);opacity:0}}`
      document.head.appendChild(style)
    }

    mapRef.current = map
    conflictLayerRef.current = conflictLayer
    osintLayerRef.current = osintLayer

    return () => {
      map.remove()
      mapRef.current = null
      conflictLayerRef.current = null
      osintLayerRef.current = null
    }
  }, [])

  // ─── Conflict/protest markers ──────────────────────────────────────────────

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

  useEffect(() => {
    const layer = conflictLayerRef.current
    if (!layer) return
    layer.clearLayers()
    markersRef.current.clear()
    for (const event of allEvents) {
      if (!isFinite(event.lat) || !isFinite(event.lon)) continue
      const isHAPI = event.dataSource === 'HAPI/OCHA'
      const icon = createThreatIcon(event.threatLevel, isHAPI)
      const marker = L.marker([event.lat, event.lon], { icon })
      marker.bindPopup(L.popup({ className: 'protest-popup', maxWidth: 240, minWidth: 180 }).setContent(buildPopupHtml(event)))
      marker.on('click', () => onSelectEvent(event))
      layer.addLayer(marker)
      markersRef.current.set(event.id, marker)
    }
  }, [allEvents, onSelectEvent])

  // Pan to selected
  useEffect(() => {
    if (!selectedEventId || !mapRef.current) return
    const marker = markersRef.current.get(selectedEventId)
    if (marker) {
      mapRef.current.flyTo(marker.getLatLng(), Math.max(mapRef.current.getZoom(), 5), { animate: true, duration: 0.8 })
      marker.openPopup()
    }
  }, [selectedEventId])

  // ─── OSINT layer markers ───────────────────────────────────────────────────

  useEffect(() => {
    const layer = osintLayerRef.current
    if (!layer || !osint) return
    layer.clearLayers()

    const { activeLayers, flights, militaryFlights, vessels, earthquakes, satellites, healthOutbreaks, datacenters, ddos } = osint

    // Civil flights ✈
    if (activeLayers.has('flights')) {
      for (const a of flights) {
        if (!isFinite(a.lat) || !isFinite(a.lon)) continue
        const marker = L.marker([a.lat, a.lon], { icon: createFlightIcon(a.heading ?? 0, '#64d2ff', 13) })
        marker.bindPopup(L.popup({ maxWidth: 220 }).setContent(flightPopup(a)))
        layer.addLayer(marker)
      }
    }

    // Military flights 🛩
    if (activeLayers.has('military_flights')) {
      for (const a of militaryFlights) {
        if (!isFinite(a.lat) || !isFinite(a.lon)) continue
        const marker = L.marker([a.lat, a.lon], { icon: createFlightIcon(a.heading ?? 0, '#ff2d55', 14) })
        marker.bindPopup(L.popup({ maxWidth: 220 }).setContent(flightPopup(a)))
        layer.addLayer(marker)
      }
    }

    // Vessels 🚢
    if (activeLayers.has('vessels')) {
      for (const v of vessels) {
        if (!isFinite(v.lat) || !isFinite(v.lon)) continue
        const marker = L.marker([v.lat, v.lon], { icon: createDotIcon('#30d158', 12, '🚢') })
        marker.bindPopup(L.popup({ maxWidth: 220 }).setContent(vesselPopup(v)))
        layer.addLayer(marker)
      }
    }

    // Earthquakes 🌋
    if (activeLayers.has('earthquakes')) {
      for (const eq of earthquakes) {
        if (!isFinite(eq.lat) || !isFinite(eq.lon)) continue
        const marker = L.marker([eq.lat, eq.lon], { icon: eqIcon(eq.magnitude ?? 3) })
        marker.bindPopup(L.popup({ maxWidth: 240 }).setContent(eqPopup(eq)))
        layer.addLayer(marker)
      }
    }

    // Satellites 🛰
    if (activeLayers.has('satellites')) {
      for (const sat of satellites) {
        if (!isFinite(sat.lat) || !isFinite(sat.lon)) continue
        const marker = L.marker([sat.lat, sat.lon], { icon: createDotIcon('#ffd60a', 10, '🛰') })
        marker.bindPopup(L.popup({ maxWidth: 200 }).setContent(
          genericPopup('🛰 Satellite', sat.name, '#ffd60a', [
            ['Category', sat.category],
            ['Orbit', sat.orbitType],
            ['Altitude', sat.altitude != null ? Math.round(sat.altitude) + ' km' : undefined],
            ['Velocity', sat.velocity_kmh != null ? Math.round(sat.velocity_kmh).toLocaleString() + ' km/h' : undefined],
            ['Agency', sat.agency],
          ])
        ))
        layer.addLayer(marker)
      }
    }

    // Health outbreaks 🏥
    if (activeLayers.has('health')) {
      for (const o of healthOutbreaks) {
        if (!isFinite(o.lat) || !isFinite(o.lon)) continue
        const marker = L.marker([o.lat, o.lon], { icon: createDotIcon('#ff375f', 12, '🏥') })
        marker.bindPopup(L.popup({ maxWidth: 220 }).setContent(
          genericPopup('🏥 Health Alert', o.disease, '#ff375f', [
            ['Disease', o.disease],
            ['Country', o.country],
            ['Status', o.status],
            ['Reported', o.reportDate],
          ])
        ))
        layer.addLayer(marker)
      }
    }

    // Datacenters 🖥
    if (activeLayers.has('datacenters')) {
      const allDC = datacenters
      for (const dc of allDC) {
        if (!isFinite(dc.lat) || !isFinite(dc.lon)) continue
        const colors: Record<string, string> = { datacenter: '#0a84ff', cloud: '#5ac8fa', exchange: '#32ade6', cable: '#30d158' }
        const color = colors[dc.type] ?? '#0a84ff'
        const emojis: Record<string, string> = { datacenter: '🖥', cloud: '☁', exchange: '🔗', cable: '🌐' }
        const emoji = emojis[dc.type] ?? '🖥'
        const marker = L.marker([dc.lat, dc.lon], { icon: createDotIcon(color, 11, emoji) })
        marker.bindPopup(L.popup({ maxWidth: 220 }).setContent(
          genericPopup(`${emoji} ${dc.type.charAt(0).toUpperCase() + dc.type.slice(1)}`, dc.name, color, [
            ['Name', dc.name],
            ['Provider', dc.provider],
            ['Location', `${dc.city}, ${dc.country}`],
            ['Tier', dc.tier],
          ])
        ))
        layer.addLayer(marker)
      }
    }

    // DDoS — country bubble markers
    if (activeLayers.has('ddos')) {
      for (const d of ddos) {
        if (!isFinite(d.lat) || !isFinite(d.lon)) continue
        const radiusKm = Math.max(40, Math.min(500, (d.attackCount / 500) * 200))
        const sevColors: Record<string, string> = { CRITICAL: '#ff2d55', HIGH: '#ff6b35', MEDIUM: '#ffd60a', LOW: '#bf5af2' }
        const color = sevColors[d.severity] ?? '#bf5af2'
        const circle = L.circle([d.lat, d.lon], {
          radius: radiusKm * 1000,
          color,
          fillColor: color,
          fillOpacity: 0.15,
          weight: 2,
          opacity: 0.7,
        })
        circle.bindPopup(L.popup({ maxWidth: 200 }).setContent(
          genericPopup('⚡ DDoS Attack', d.country, color, [
            ['Country', d.country],
            ['Severity', d.severity],
            ['Attacks', d.attackCount?.toLocaleString()],
            ['Bandwidth', d.bandwidth ? d.bandwidth + ' Gbps' : undefined],
          ])
        ))
        layer.addLayer(circle)
      }
    }

  }, [osint])

  // Active layer count for badge
  const osintCount = useMemo(() => {
    if (!osint) return 0
    let n = 0
    if (osint.activeLayers.has('flights')) n += osint.flights.length
    if (osint.activeLayers.has('military_flights')) n += osint.militaryFlights.length
    if (osint.activeLayers.has('vessels')) n += osint.vessels.length
    if (osint.activeLayers.has('earthquakes')) n += osint.earthquakes.length
    if (osint.activeLayers.has('satellites')) n += osint.satellites.length
    if (osint.activeLayers.has('health')) n += osint.healthOutbreaks.length
    if (osint.activeLayers.has('datacenters')) n += osint.datacenters.length
    return n
  }, [osint])

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full" />

      {/* Legend */}
      <div className="absolute bottom-8 left-3 z-[1000] bg-[#0d1b2e]/90 border border-[#1e3a5f] rounded-lg p-2.5 backdrop-blur-sm">
        <p className="text-[9px] text-[#8ba3c0] uppercase tracking-wider mb-1.5 font-semibold">Threat Level</p>
        {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((level) => {
          const cfg = THREAT_CONFIG[level]
          return (
            <div key={level} className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: cfg.color }} />
              <span className="text-[10px]" style={{ color: cfg.color }}>{cfg.label}</span>
            </div>
          )
        })}
        {osint && (
          <div className="mt-1.5 pt-1.5 border-t border-[#1e3a5f] space-y-1">
            {osint.activeLayers.has('flights') && <div className="flex items-center gap-1.5"><span className="text-[10px]">✈</span><span className="text-[10px] text-[#64d2ff]">Flights ({osint.flights.length})</span></div>}
            {osint.activeLayers.has('military_flights') && <div className="flex items-center gap-1.5"><span className="text-[10px]">🛩</span><span className="text-[10px] text-[#ff2d55]">Military ({osint.militaryFlights.length})</span></div>}
            {osint.activeLayers.has('vessels') && <div className="flex items-center gap-1.5"><span className="text-[10px]">🚢</span><span className="text-[10px] text-[#30d158]">Vessels ({osint.vessels.length})</span></div>}
            {osint.activeLayers.has('earthquakes') && <div className="flex items-center gap-1.5"><span className="text-[10px]">🌋</span><span className="text-[10px] text-[#ff9f0a]">Quakes ({osint.earthquakes.length})</span></div>}
            {osint.activeLayers.has('satellites') && <div className="flex items-center gap-1.5"><span className="text-[10px]">🛰</span><span className="text-[10px] text-[#ffd60a]">Satellites ({osint.satellites.length})</span></div>}
          </div>
        )}
      </div>

      {/* No-data notice when flights enabled but empty */}
      {osint?.activeLayers.has('flights') && osint.flights.length === 0 && (
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[1000] bg-[#0d1b2e]/90 border border-[#64d2ff]/30 rounded-xl px-5 py-4 text-center pointer-events-none max-w-xs">
          <div className="text-2xl mb-2">✈</div>
          <p className="text-[#e8f0fe] text-sm font-semibold">Fetching Live Flights…</p>
          <p className="text-[#8ba3c0] text-[11px] mt-1">Connecting to OpenSky Network, adsb.lol, and airplanes.live</p>
          <p className="text-[#8ba3c0]/60 text-[10px] mt-2">Ensure backend is running at localhost:8000</p>
        </div>
      )}

      {/* Event count badge */}
      <div className="absolute top-3 left-3 z-[1000] bg-[#0d1b2e]/90 border border-[#1e3a5f] rounded-lg px-2.5 py-1.5 backdrop-blur-sm flex items-center gap-2">
        {osint?.activeLayers.has('flights') && (
          <span className="text-[10px] text-[#64d2ff] font-bold">
            ✈ {osint.flights.length} flights live
          </span>
        )}
        {allEvents.length > 0 && (
        <span className="text-[10px] text-[#8ba3c0]">
          Events: <span className="text-[#64d2ff] font-bold">{allEvents.length}</span>
        </span>
        )}
        {osintCount > 0 && (
          <span className="text-[10px] text-[#8ba3c0]">
            | OSINT: <span className="text-[#ffd60a] font-bold">{osintCount}</span>
          </span>
        )}
      </div>
    </div>
  )
}

export default ProtestMap
