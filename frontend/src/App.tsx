import React, { useState, useMemo, useCallback } from 'react'
import { RefreshCw, Wifi, WifiOff, Globe, Map, Video, List, AlertTriangle, Globe2 } from 'lucide-react'
import clsx from 'clsx'
import type { ProtestEvent, HAPIEvent, FilterState } from './types/protest'
import { DEFAULT_FILTERS } from './types/protest'
import type { LayerKey } from './types/osint'
import { useProtestMap, useStreams } from './hooks/useProtestMap'
import {
  useFlights,
  useMilitaryFlights,
  useVessels,
  useEarthquakes,
  useDDoS,
  useSatellites,
  useHealth,
  useDatacenters,
  useSocialFeeds,
  useNewsIntel,
} from './hooks/useOSINTLayers'
import { StatsBar } from './components/StatsBar'
import { FilterBar } from './components/FilterBar'
import { EventSidebar } from './components/EventSidebar'
import { VideoPanel } from './components/VideoPanel'
import { EventModal } from './components/EventModal'
import { ProtestMap } from './components/ProtestMap'
import type { OSINTLayerData } from './components/ProtestMap'
import { OSINTGlobe } from './components/OSINTGlobe'
import { LayerControl } from './components/LayerControl'
import { SocialFeedTicker } from './components/SocialFeedTicker'

type AnyEvent = ProtestEvent | HAPIEvent
type PanelTab = 'events' | 'video'
type ViewMode = 'split' | 'fullmap' | 'fulllist' | 'globe3d'

const LiveBadge: React.FC = () => (
  <div className="flex items-center gap-1.5">
    <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
    <span className="text-red-400 text-xs font-bold tracking-wider">LIVE</span>
  </div>
)

const Header: React.FC<{
  online: boolean
  onRefresh: () => void
  viewMode: ViewMode
  onViewMode: (v: ViewMode) => void
}> = ({ online, onRefresh, viewMode, onViewMode }) => (
  <header className="flex-shrink-0 bg-[#0a0f1e]/95 backdrop-blur-sm border-b border-[#1e3a5f] z-50">
    <div className="flex items-center gap-3 px-4 py-2.5">
      <div className="flex items-center gap-2.5 flex-shrink-0">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-red-600 to-orange-500 flex items-center justify-center flex-shrink-0">
          <Globe className="w-4 h-4 text-white" />
        </div>
        <div>
          <h1 className="text-[#e8f0fe] font-bold text-sm leading-tight">OSINT Intelligence Map</h1>
          <p className="text-[#8ba3c0] text-[10px] leading-tight">Global Multi-Domain Intelligence Platform</p>
        </div>
      </div>

      <div className="h-6 w-px bg-[#1e3a5f] mx-1 flex-shrink-0" />
      <LiveBadge />

      <div className="flex items-center gap-1 ml-3">
        {(
          [
            { id: 'split' as const, icon: <List className="w-3.5 h-3.5" />, label: 'Split' },
            { id: 'fullmap' as const, icon: <Map className="w-3.5 h-3.5" />, label: '2D Map' },
            { id: 'globe3d' as const, icon: <Globe2 className="w-3.5 h-3.5" />, label: '3D Globe' },
            { id: 'fulllist' as const, icon: <List className="w-3.5 h-3.5" />, label: 'List' },
          ]
        ).map(({ id, icon, label }) => (
          <button
            key={id}
            onClick={() => onViewMode(id)}
            title={label}
            className={clsx(
              'flex items-center gap-1 px-2 py-1 rounded text-xs transition-all border',
              viewMode === id
                ? id === 'globe3d'
                  ? 'bg-[#1e3a5f] border-[#ffd60a] text-[#ffd60a]'
                  : 'bg-[#1e3a5f] border-[#64d2ff] text-[#64d2ff]'
                : 'bg-transparent border-[#1e3a5f] text-[#8ba3c0] hover:text-[#e8f0fe]'
            )}
          >
            {icon}
            <span className="hidden sm:inline">{label}</span>
          </button>
        ))}
      </div>

      <div className="flex items-center gap-2 ml-auto">
        <div className="flex items-center gap-1.5 text-xs">
          {online ? (
            <Wifi className="w-3.5 h-3.5 text-emerald-400" />
          ) : (
            <WifiOff className="w-3.5 h-3.5 text-red-400" />
          )}
          <span className={online ? 'text-emerald-400' : 'text-red-400'}>
            {online ? 'Online' : 'Offline'}
          </span>
        </div>
        <button
          onClick={onRefresh}
          className="flex items-center gap-1.5 px-2.5 py-1.5 bg-[#1e3a5f]/60 hover:bg-[#1e3a5f] border border-[#1e3a5f] rounded-lg text-[#8ba3c0] hover:text-[#e8f0fe] transition-all text-xs"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Refresh</span>
        </button>
      </div>
    </div>
  </header>
)

const App: React.FC = () => {
  // UI state
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS)
  const [selectedEvent, setSelectedEvent] = useState<AnyEvent | null>(null)
  const [modalEvent, setModalEvent] = useState<AnyEvent | null>(null)
  const [panelTab, setPanelTab] = useState<PanelTab>('events')
  const [viewMode, setViewMode] = useState<ViewMode>('split')
  const [online, setOnline] = useState(navigator.onLine)

  // ─── OSINT layer state — lives here so it persists across 2D / 3D views ───
  const [activeLayers, setActiveLayers] = useState<Set<LayerKey>>(
    new Set<LayerKey>(['conflicts'])
  )

  const handleToggleLayer = useCallback((key: LayerKey) => {
    setActiveLayers((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }, [])

  React.useEffect(() => {
    const on = () => setOnline(true)
    const off = () => setOnline(false)
    window.addEventListener('online', on)
    window.addEventListener('offline', off)
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off) }
  }, [])

  // ─── Core protest data ─────────────────────────────────────────────────────
  const { data: mapData, isLoading: mapLoading, refetch } = useProtestMap()
  const { data: streamData, isLoading: streamLoading } = useStreams()

  const protests = useMemo<ProtestEvent[]>(() => mapData?.protests?.events ?? [], [mapData])
  const hapiEvents = useMemo<HAPIEvent[]>(() => mapData?.hapiEvents?.conflictEvents ?? [], [mapData])
  const streams = useMemo(() => streamData?.liveStreams ?? [], [streamData])
  const images = useMemo(() => streamData?.images ?? [], [streamData])
  const threatSummary = mapData?.protests?.threatSummary ?? null
  const lastUpdated = mapData?.lastUpdated ?? null
  const countriesCount = useMemo(() => {
    const s = new Set<string>()
    protests.forEach((e) => s.add(e.country))
    hapiEvents.forEach((e) => s.add(e.country))
    return s.size
  }, [protests, hapiEvents])
  const totalEvents = protests.length + hapiEvents.length

  // ─── OSINT layer data — fetched once, passed to both 2D and 3D ────────────
  const { data: flightsData, isLoading: flightsLoading } = useFlights(activeLayers.has('flights'))
  const { data: milData, isLoading: milLoading } = useMilitaryFlights(activeLayers.has('military_flights'))
  const { data: vesselData, isLoading: vesselLoading } = useVessels(activeLayers.has('vessels'))
  const { data: eqData, isLoading: eqLoading } = useEarthquakes(activeLayers.has('earthquakes'))
  const { data: ddosData, isLoading: ddosLoading } = useDDoS(activeLayers.has('ddos'))
  const { data: satData, isLoading: satLoading } = useSatellites(activeLayers.has('satellites'))
  const { data: healthData, isLoading: healthLoading } = useHealth(activeLayers.has('health'))
  const { data: dcData, isLoading: dcLoading } = useDatacenters(activeLayers.has('datacenters'))
  const { data: socialData, isLoading: socialLoading } = useSocialFeeds(true)  // always fetch
  const { data: newsData, isLoading: newsLoading } = useNewsIntel(activeLayers.has('news_intel'))

  const loadingLayers = useMemo(() => {
    const s = new Set<LayerKey>()
    if (flightsLoading && activeLayers.has('flights')) s.add('flights')
    if (milLoading && activeLayers.has('military_flights')) s.add('military_flights')
    if (vesselLoading && activeLayers.has('vessels')) s.add('vessels')
    if (eqLoading && activeLayers.has('earthquakes')) s.add('earthquakes')
    if (ddosLoading && activeLayers.has('ddos')) s.add('ddos')
    if (satLoading && activeLayers.has('satellites')) s.add('satellites')
    if (healthLoading && activeLayers.has('health')) s.add('health')
    if (dcLoading && activeLayers.has('datacenters')) s.add('datacenters')
    return s
  }, [flightsLoading, milLoading, vesselLoading, eqLoading, ddosLoading, satLoading, healthLoading, dcLoading, activeLayers])

  // Merged datacenter list
  const allDatacenters = useMemo(() => [
    ...(dcData?.datacenters ?? []),
    ...(dcData?.cloudRegions ?? []),
    ...(dcData?.internetExchanges ?? []),
  ], [dcData])

  // OSINT data bundle passed to 2D map
  const osintLayerData = useMemo<OSINTLayerData>(() => ({
    flights: flightsData?.aircraft ?? [],
    militaryFlights: milData?.aircraft ?? [],
    vessels: vesselData?.vessels ?? [],
    earthquakes: eqData?.events ?? [],
    ddos: ddosData?.countries ?? [],
    satellites: satData?.satellites ?? [],
    healthOutbreaks: healthData?.outbreaks ?? [],
    datacenters: allDatacenters,
    activeLayers,
  }), [flightsData, milData, vesselData, eqData, ddosData, satData, healthData, allDatacenters, activeLayers])

  const handleSelectEvent = useCallback((e: AnyEvent) => {
    setSelectedEvent(e)
    setModalEvent(e)
  }, [])

  // ─── Shared LayerControl overlay (renders on top of whichever map is active)
  const LayerOverlay = (
    <div className="absolute top-3 right-3 z-[1100]">
      <LayerControl
        activeLayers={activeLayers}
        onToggleLayer={handleToggleLayer}
        loadingLayers={loadingLayers}
      />
    </div>
  )

  // ─── 3D Globe view ────────────────────────────────────────────────────────
  if (viewMode === 'globe3d') {
    return (
      <div className="flex flex-col h-screen bg-[#020810] text-[#e8f0fe] overflow-hidden">
        <Header online={online} onRefresh={() => refetch()} viewMode={viewMode} onViewMode={setViewMode} />
        <div className="flex-1 overflow-hidden relative">
          <OSINTGlobe
            protests={protests}
            hapiEvents={hapiEvents}
            activeLayers={activeLayers}
            loadingLayers={loadingLayers}
            flights={flightsData?.aircraft ?? []}
            militaryFlights={milData?.aircraft ?? []}
            vessels={vesselData?.vessels ?? []}
            earthquakes={eqData?.events ?? []}
            ddos={ddosData?.countries ?? []}
            satellites={satData?.satellites ?? []}
            healthOutbreaks={healthData?.outbreaks ?? []}
            datacenters={allDatacenters}
            socialData={socialData ?? null}
            newsData={newsData ?? null}
            socialLoading={socialLoading}
            newsLoading={newsLoading}
          />
          {/* Layer control on globe */}
          <div className="absolute top-3 right-3 z-[1100]">
            <LayerControl
              activeLayers={activeLayers}
              onToggleLayer={handleToggleLayer}
              loadingLayers={loadingLayers}
            />
          </div>
        </div>
        {/* Social feed ticker always at bottom */}
        <SocialFeedTicker data={socialData} loading={socialLoading} />
      </div>
    )
  }

  // ─── 2D / Split / List views ──────────────────────────────────────────────
  return (
    <div className="flex flex-col h-screen bg-[#0a0f1e] text-[#e8f0fe] overflow-hidden">
      <Header online={online} onRefresh={() => refetch()} viewMode={viewMode} onViewMode={setViewMode} />

      {/* Stats + Filter bar */}
      <div className="flex-shrink-0 border-b border-[#1e3a5f] bg-[#0a0f1e]/90 px-4 py-2 space-y-2">
        <StatsBar
          totalEvents={totalEvents}
          threatSummary={threatSummary}
          countriesCount={countriesCount}
          isLive={!mapLoading}
          lastUpdated={lastUpdated}
        />
        <FilterBar filters={filters} onChange={setFilters} />
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Map */}
        {viewMode !== 'fulllist' && (
          <div className="relative flex-1 overflow-hidden">
            {mapLoading && (
              <div className="absolute inset-0 z-20 flex items-center justify-center bg-[#0a0f1e]/80 pointer-events-none">
                <div className="flex flex-col items-center gap-3">
                  <div className="w-8 h-8 border-2 border-[#64d2ff] border-t-transparent rounded-full animate-spin" />
                  <span className="text-[#8ba3c0] text-sm">Aggregating intelligence data…</span>
                  <span className="text-[#8ba3c0] text-xs">GDELT · HAPI/OCHA · OpenSky · USGS</span>
                </div>
              </div>
            )}
            <ProtestMap
              protests={protests}
              hapiEvents={hapiEvents}
              filters={filters}
              selectedEventId={selectedEvent?.id ?? null}
              onSelectEvent={handleSelectEvent}
              osint={osintLayerData}
            />
            {/* Layer control overlay — visible in all 2D map modes */}
            {LayerOverlay}
          </div>
        )}

        {/* Side panel */}
        {viewMode !== 'fullmap' && (
          <div className={clsx(
            'flex flex-col bg-[#0d1b2e] border-l border-[#1e3a5f] overflow-hidden',
            viewMode === 'fulllist' ? 'flex-1' : 'w-80 xl:w-96 flex-shrink-0'
          )}>
            {/* Tabs */}
            <div className="flex border-b border-[#1e3a5f] flex-shrink-0">
              <button
                onClick={() => setPanelTab('events')}
                className={clsx(
                  'flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 transition-all',
                  panelTab === 'events' ? 'border-[#64d2ff] text-[#64d2ff]' : 'border-transparent text-[#8ba3c0] hover:text-[#e8f0fe]'
                )}
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                Events
                <span className="ml-1 bg-[#1e3a5f] text-[#64d2ff] text-[9px] px-1.5 py-0.5 rounded-full font-bold">
                  {totalEvents}
                </span>
              </button>
              <button
                onClick={() => setPanelTab('video')}
                className={clsx(
                  'flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 transition-all',
                  panelTab === 'video' ? 'border-red-500 text-red-400' : 'border-transparent text-[#8ba3c0] hover:text-[#e8f0fe]'
                )}
              >
                <Video className="w-3.5 h-3.5" />
                Live Video
                {streams.length > 0 && (
                  <span className="ml-1 bg-red-500/20 text-red-400 text-[9px] px-1.5 py-0.5 rounded-full font-bold">
                    {streams.length}
                  </span>
                )}
              </button>
            </div>

            <div className="flex-1 overflow-hidden flex flex-col">
              {panelTab === 'events' ? (
                <EventSidebar
                  protests={protests}
                  hapiEvents={hapiEvents}
                  filters={filters}
                  selectedEventId={selectedEvent?.id ?? null}
                  onSelectEvent={handleSelectEvent}
                  loading={mapLoading}
                />
              ) : (
                <VideoPanel streams={streams} images={images} loading={streamLoading} />
              )}
            </div>

            {/* Footer */}
            <div className="flex-shrink-0 border-t border-[#1e3a5f] px-3 py-2">
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-[9px] text-[#8ba3c0] uppercase tracking-wider">Sources:</span>
                {['GDELT', 'HAPI/OCHA', 'ACLED*', 'OpenSky', 'USGS', 'Celestrak', 'WHO'].map((src) => (
                  <span key={src} className="text-[9px] px-1.5 py-0.5 bg-[#1e3a5f]/60 border border-[#1e3a5f] rounded text-[#64d2ff]">
                    {src}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Layer control for fulllist mode (no map visible) */}
        {viewMode === 'fulllist' && (
          <div className="fixed bottom-12 right-4 z-[1100]">
            <LayerControl
              activeLayers={activeLayers}
              onToggleLayer={handleToggleLayer}
              loadingLayers={loadingLayers}
            />
          </div>
        )}
      </div>

      {/* Social feed ticker — fixed at the very bottom */}
      <SocialFeedTicker data={socialData} loading={socialLoading} />

      {/* Event modal */}
      {modalEvent && <EventModal event={modalEvent} onClose={() => setModalEvent(null)} />}
    </div>
  )
}

export default App
