/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useRef, useEffect, useMemo, useCallback, useState } from 'react'
// react-globe.gl is a JavaScript library; use a loose import to avoid type conflicts
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import GlobeGL from 'react-globe.gl'
import type {
  Aircraft,
  MilitaryAircraft,
  Vessel,
  Earthquake,
  DDoSCountry,
  Satellite,
  HealthOutbreak,
  DatacenterFacility,
  GlobePoint,
  LayerKey,
} from '../types/osint'
import type { ProtestEvent, HAPIEvent } from '../types/protest'

interface Globe3DProps {
  // Layer data
  flights?: Aircraft[]
  militaryFlights?: MilitaryAircraft[]
  vessels?: Vessel[]
  earthquakes?: Earthquake[]
  ddos?: DDoSCountry[]
  satellites?: Satellite[]
  protests?: ProtestEvent[]
  hapiEvents?: HAPIEvent[]
  healthOutbreaks?: HealthOutbreak[]
  datacenters?: DatacenterFacility[]

  // Active layers
  activeLayers: Set<LayerKey>

  // Interaction
  onPointClick?: (point: GlobePoint) => void
  selectedPointId?: string | null
}

// Color helpers
const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#ff2d55',
  HIGH: '#ff6b35',
  MEDIUM: '#ffd60a',
  LOW: '#30d158',
  INFO: '#64d2ff',
}

function severityToColor(severity: string): string {
  return SEVERITY_COLORS[severity] ?? '#64d2ff'
}

// Convert all layer data into unified GlobePoint arrays
function buildPoints(
  activeLayers: Set<LayerKey>,
  flights: Aircraft[],
  militaryFlights: MilitaryAircraft[],
  vessels: Vessel[],
  earthquakes: Earthquake[],
  satellites: Satellite[],
  protests: ProtestEvent[],
  hapiEvents: HAPIEvent[],
  healthOutbreaks: HealthOutbreak[],
  datacenters: DatacenterFacility[]
): GlobePoint[] {
  const points: GlobePoint[] = []

  if (activeLayers.has('flights')) {
    flights.forEach((a) => {
      if (a.lat && a.lon) {
        points.push({
          lat: a.lat,
          lng: a.lon,
          size: 0.4,
          color: '#64d2ff',
          label: `✈ ${a.callsign || a.icao24} (${a.country})\nAlt: ${a.altitude != null ? Math.round(a.altitude) : '?'}m | ${a.velocity != null ? Math.round(a.velocity) : '?'}km/h`,
          data: a,
          layer: 'flights',
        })
      }
    })
  }

  if (activeLayers.has('military_flights')) {
    militaryFlights.forEach((a) => {
      if (a.lat && a.lon) {
        points.push({
          lat: a.lat,
          lng: a.lon,
          size: 0.6,
          color: '#ff2d55',
          label: `🛩 ${a.callsign || a.icao24} [MIL]\n${a.nation || a.country}\nAlt: ${a.altitude != null ? Math.round(a.altitude) : '?'}m`,
          data: a,
          layer: 'military_flights',
        })
      }
    })
  }

  if (activeLayers.has('vessels')) {
    vessels.forEach((v) => {
      if (v.lat && v.lon) {
        points.push({
          lat: v.lat,
          lng: v.lon,
          size: 0.5,
          color: '#30d158',
          label: `🚢 ${v.name}\nType: ${v.type || v.shipType || 'Unknown'}\nSpeed: ${v.speed}kts${v.destination ? `\nDest: ${v.destination}` : ''}`,
          data: v,
          layer: 'vessels',
        })
      }
    })
  }

  if (activeLayers.has('earthquakes')) {
    earthquakes.forEach((eq) => {
      if (eq.lat && eq.lon) {
        const size = Math.max(0.3, Math.min(2.5, (eq.magnitude - 2) * 0.5))
        points.push({
          lat: eq.lat,
          lng: eq.lon,
          size,
          color: severityToColor(eq.severity),
          label: `🌋 M${eq.magnitude.toFixed(1)} - ${eq.place}\nDepth: ${eq.depth}km${eq.tsunami ? ' | TSUNAMI WARNING' : ''}`,
          data: eq,
          layer: 'earthquakes',
        })
      }
    })
  }

  if (activeLayers.has('satellites')) {
    satellites.forEach((sat) => {
      if (sat.lat != null && sat.lon != null) {
        points.push({
          lat: sat.lat,
          lng: sat.lon,
          size: 0.3,
          color: '#ffd60a',
          label: `🛰 ${sat.name}\nAlt: ${Math.round(sat.altitude)}km\nType: ${sat.category}`,
          data: sat,
          layer: 'satellites',
        })
      }
    })
  }

  if (activeLayers.has('conflicts')) {
    protests.forEach((p) => {
      if (p.lat && p.lon) {
        points.push({
          lat: p.lat,
          lng: p.lon,
          size: 0.5,
          color: severityToColor(p.threatLevel),
          label: `🔥 ${p.title}\n${p.country} | ${p.threatLevel}`,
          data: p,
          layer: 'conflicts',
        })
      }
    })
    hapiEvents.forEach((h) => {
      if (h.lat && h.lon) {
        points.push({
          lat: h.lat,
          lng: h.lon,
          size: 0.45,
          color: severityToColor(h.threatLevel),
          label: `⚠ ${h.eventType}\n${h.country} | Fatalities: ${h.fatalities}`,
          data: h,
          layer: 'conflicts',
        })
      }
    })
  }

  if (activeLayers.has('health')) {
    healthOutbreaks.forEach((o) => {
      if (o.lat && o.lon) {
        points.push({
          lat: o.lat,
          lng: o.lon,
          size: 0.6,
          color: '#ff375f',
          label: `🏥 ${o.disease}\n${o.country} | ${o.status}\n${o.reportDate}`,
          data: o,
          layer: 'health',
        })
      }
    })
  }

  if (activeLayers.has('datacenters')) {
    datacenters.forEach((dc) => {
      if (dc.lat && dc.lon) {
        const colors: Record<string, string> = {
          datacenter: '#0a84ff',
          cloud: '#5ac8fa',
          exchange: '#32ade6',
          cable: '#30d158',
        }
        points.push({
          lat: dc.lat,
          lng: dc.lon,
          size: 0.4,
          color: colors[dc.type] ?? '#0a84ff',
          label: `🖥 ${dc.name}\n${dc.provider} | ${dc.city}, ${dc.country}\nType: ${dc.type}`,
          data: dc,
          layer: 'datacenters',
        })
      }
    })
  }

  return points
}

// DDoS rings (country-level bubbles)
function buildDDoSRings(ddos: DDoSCountry[], active: boolean) {
  if (!active) return []
  return ddos.map((d) => ({
    lat: d.lat,
    lng: d.lon,
    maxR: Math.max(1, Math.min(8, (d.attackCount / 1000) * 3)),
    propagationSpeed: 2,
    repeatPeriod: 700,
    color: severityToColor(d.severity),
    label: `⚡ DDoS: ${d.country}\nAttacks: ${d.attackCount.toLocaleString()}${d.bandwidth ? `\nBandwidth: ${d.bandwidth}Gbps` : ''}`,
    data: d,
  }))
}

export const Globe3D: React.FC<Globe3DProps> = ({
  flights = [],
  militaryFlights = [],
  vessels = [],
  earthquakes = [],
  ddos = [],
  satellites = [],
  protests = [],
  hapiEvents = [],
  healthOutbreaks = [],
  datacenters = [],
  activeLayers,
  onPointClick,
}) => {
  const globeRef = useRef<any>(null)
  const [tooltipContent, setTooltipContent] = useState<string | null>(null)
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 })

  // Auto-rotate
  useEffect(() => {
    if (globeRef.current) {
      const controls = globeRef.current.controls?.()
      if (controls) {
        controls.autoRotate = true
        controls.autoRotateSpeed = 0.3
      }
    }
  }, [])

  const points = useMemo(
    () =>
      buildPoints(
        activeLayers,
        flights,
        militaryFlights,
        vessels,
        earthquakes,
        satellites,
        protests,
        hapiEvents,
        healthOutbreaks,
        datacenters
      ),
    [activeLayers, flights, militaryFlights, vessels, earthquakes, satellites, protests, hapiEvents, healthOutbreaks, datacenters]
  )

  const ddosRings = useMemo(
    () => buildDDoSRings(ddos, activeLayers.has('ddos')),
    [ddos, activeLayers]
  )

  const handlePointHover = useCallback(
    (point: any, _prevPoint: any, event: any) => {
      if (point) {
        setTooltipContent((point as GlobePoint).label)
        setTooltipPos({ x: event?.clientX ?? 0, y: event?.clientY ?? 0 })
      } else {
        setTooltipContent(null)
      }
    },
    []
  )

  const handlePointClick = useCallback(
    (point: any) => {
      onPointClick?.(point as GlobePoint)
    },
    [onPointClick]
  )

  return (
    <div className="relative w-full h-full bg-[#020810]">
      <GlobeGL
        ref={globeRef}
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
        bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
        backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
        // Points layer
        pointsData={points}
        pointLat={(d: any) => d.lat}
        pointLng={(d: any) => d.lng}
        pointColor={(d: any) => d.color}
        pointAltitude={0.01}
        pointRadius={(d: any) => d.size}
        pointResolution={6}
        onPointHover={handlePointHover as any}
        onPointClick={handlePointClick}
        pointsMerge={false}
        // Rings for DDoS
        ringsData={ddosRings}
        ringLat={(d: any) => d.lat}
        ringLng={(d: any) => d.lng}
        ringMaxRadius={(d: any) => d.maxR}
        ringPropagationSpeed={(d: any) => d.propagationSpeed}
        ringRepeatPeriod={(d: any) => d.repeatPeriod}
        ringColor={(d: any) => d.color}
        // Atmosphere
        showAtmosphere={true}
        atmosphereColor="#1a4a8a"
        atmosphereAltitude={0.12}
        // Rendering
        rendererConfig={{ antialias: true, alpha: true }}
      />

      {/* Tooltip */}
      {tooltipContent && (
        <div
          className="fixed z-50 pointer-events-none bg-[#0d1b2e]/95 border border-[#1e3a5f] rounded-lg px-3 py-2 shadow-xl"
          style={{ left: tooltipPos.x + 12, top: tooltipPos.y - 10, maxWidth: 260 }}
        >
          {tooltipContent.split('\n').map((line, i) => (
            <div
              key={i}
              className={i === 0 ? 'text-[#e8f0fe] text-xs font-semibold' : 'text-[#8ba3c0] text-[11px] mt-0.5'}
            >
              {line}
            </div>
          ))}
        </div>
      )}

      {/* Point count badges */}
      <div className="absolute bottom-4 left-4 flex flex-wrap gap-1.5 max-w-xs">
        {activeLayers.has('flights') && flights.length > 0 && (
          <Badge color="#64d2ff" icon="✈" count={flights.length} label="Flights" />
        )}
        {activeLayers.has('military_flights') && militaryFlights.length > 0 && (
          <Badge color="#ff2d55" icon="🛩" count={militaryFlights.length} label="Military" />
        )}
        {activeLayers.has('vessels') && vessels.length > 0 && (
          <Badge color="#30d158" icon="🚢" count={vessels.length} label="Vessels" />
        )}
        {activeLayers.has('earthquakes') && earthquakes.length > 0 && (
          <Badge color="#ff9f0a" icon="🌋" count={earthquakes.length} label="Quakes" />
        )}
        {activeLayers.has('ddos') && ddos.length > 0 && (
          <Badge color="#bf5af2" icon="⚡" count={ddos.length} label="DDoS" />
        )}
        {activeLayers.has('satellites') && satellites.length > 0 && (
          <Badge color="#ffd60a" icon="🛰" count={satellites.length} label="Satellites" />
        )}
        {activeLayers.has('conflicts') && (protests.length + hapiEvents.length) > 0 && (
          <Badge color="#ff6b35" icon="🔥" count={protests.length + hapiEvents.length} label="Conflicts" />
        )}
        {activeLayers.has('health') && healthOutbreaks.length > 0 && (
          <Badge color="#ff375f" icon="🏥" count={healthOutbreaks.length} label="Health" />
        )}
        {activeLayers.has('datacenters') && datacenters.length > 0 && (
          <Badge color="#0a84ff" icon="🖥" count={datacenters.length} label="Infra" />
        )}
      </div>
    </div>
  )
}

const Badge: React.FC<{
  color: string
  icon: string
  count: number
  label: string
}> = ({ color, icon, count, label }) => (
  <div
    className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold"
    style={{
      backgroundColor: `${color}22`,
      border: `1px solid ${color}66`,
      color,
    }}
  >
    <span>{icon}</span>
    <span>{count.toLocaleString()}</span>
    <span className="opacity-70">{label}</span>
  </div>
)
