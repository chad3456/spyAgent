import React, { useState, useMemo, useCallback } from 'react'
import { RefreshCw, Wifi, WifiOff, Globe, Map, Video, List, AlertTriangle, Globe2 } from 'lucide-react'
import clsx from 'clsx'
import type { ProtestEvent, HAPIEvent, FilterState } from './types/protest'
import { DEFAULT_FILTERS } from './types/protest'
import { useProtestMap, useStreams } from './hooks/useProtestMap'
import { StatsBar } from './components/StatsBar'
import { FilterBar } from './components/FilterBar'
import { EventSidebar } from './components/EventSidebar'
import { VideoPanel } from './components/VideoPanel'
import { EventModal } from './components/EventModal'
import { ProtestMap } from './components/ProtestMap'
import { OSINTGlobe } from './components/OSINTGlobe'

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
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS)
  const [selectedEvent, setSelectedEvent] = useState<AnyEvent | null>(null)
  const [modalEvent, setModalEvent] = useState<AnyEvent | null>(null)
  const [panelTab, setPanelTab] = useState<PanelTab>('events')
  const [viewMode, setViewMode] = useState<ViewMode>('split')
  const [online, setOnline] = useState(navigator.onLine)

  React.useEffect(() => {
    const on = () => setOnline(true)
    const off = () => setOnline(false)
    window.addEventListener('online', on)
    window.addEventListener('offline', off)
    return () => {
      window.removeEventListener('online', on)
      window.removeEventListener('offline', off)
    }
  }, [])

  const { data: mapData, isLoading: mapLoading, refetch } = useProtestMap()
  const { data: streamData, isLoading: streamLoading } = useStreams()

  const protests = useMemo<ProtestEvent[]>(() => mapData?.protests?.events ?? [], [mapData])
  const hapiEvents = useMemo<HAPIEvent[]>(() => mapData?.hapiEvents?.conflictEvents ?? [], [mapData])
  const streams = useMemo(() => streamData?.liveStreams ?? [], [streamData])
  const images = useMemo(() => streamData?.images ?? [], [streamData])

  const threatSummary = mapData?.protests?.threatSummary ?? null
  const lastUpdated = mapData?.lastUpdated ?? null

  const countriesCount = useMemo(() => {
    const set = new Set<string>()
    protests.forEach((e) => set.add(e.country))
    hapiEvents.forEach((e) => set.add(e.country))
    return set.size
  }, [protests, hapiEvents])

  const totalEvents = protests.length + hapiEvents.length

  const handleSelectEvent = useCallback((e: AnyEvent) => {
    setSelectedEvent(e)
    setModalEvent(e)
  }, [])

  // Full-screen 3D globe mode
  if (viewMode === 'globe3d') {
    return (
      <div className="flex flex-col h-screen bg-[#020810] text-[#e8f0fe] overflow-hidden">
        <Header
          online={online}
          onRefresh={() => refetch()}
          viewMode={viewMode}
          onViewMode={setViewMode}
        />
        <div className="flex-1 overflow-hidden">
          <OSINTGlobe protests={protests} hapiEvents={hapiEvents} />
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-[#0a0f1e] text-[#e8f0fe] overflow-hidden">
      <Header
        online={online}
        onRefresh={() => refetch()}
        viewMode={viewMode}
        onViewMode={setViewMode}
      />

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
              <div className="absolute inset-0 z-20 flex items-center justify-center bg-[#0a0f1e]/80">
                <div className="flex flex-col items-center gap-3">
                  <div className="w-8 h-8 border-2 border-[#64d2ff] border-t-transparent rounded-full animate-spin" />
                  <span className="text-[#8ba3c0] text-sm">Aggregating global intelligence data…</span>
                  <span className="text-[#8ba3c0] text-xs">GDELT · HAPI/OCHA · ACLED · OpenSky · USGS</span>
                </div>
              </div>
            )}
            <ProtestMap
              protests={protests}
              hapiEvents={hapiEvents}
              filters={filters}
              selectedEventId={selectedEvent?.id ?? null}
              onSelectEvent={handleSelectEvent}
            />
          </div>
        )}

        {/* Side panel */}
        {viewMode !== 'fullmap' && (
          <div
            className={clsx(
              'flex flex-col bg-[#0d1b2e] border-l border-[#1e3a5f] overflow-hidden',
              viewMode === 'fulllist' ? 'flex-1' : 'w-80 xl:w-96 flex-shrink-0'
            )}
          >
            {/* Panel tabs */}
            <div className="flex border-b border-[#1e3a5f] flex-shrink-0">
              <button
                onClick={() => setPanelTab('events')}
                className={clsx(
                  'flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 transition-all',
                  panelTab === 'events'
                    ? 'border-[#64d2ff] text-[#64d2ff]'
                    : 'border-transparent text-[#8ba3c0] hover:text-[#e8f0fe]'
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
                  panelTab === 'video'
                    ? 'border-red-500 text-red-400'
                    : 'border-transparent text-[#8ba3c0] hover:text-[#e8f0fe]'
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

            {/* Source attribution footer */}
            <div className="flex-shrink-0 border-t border-[#1e3a5f] px-3 py-2">
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-[9px] text-[#8ba3c0] uppercase tracking-wider">Sources:</span>
                {['GDELT', 'HAPI/OCHA', 'ACLED*', 'OpenSky', 'USGS', 'Celestrak'].map((src) => (
                  <span
                    key={src}
                    className="text-[9px] px-1.5 py-0.5 bg-[#1e3a5f]/60 border border-[#1e3a5f] rounded text-[#64d2ff]"
                  >
                    {src}
                  </span>
                ))}
                <span className="text-[9px] text-[#8ba3c0] ml-auto">*env key required</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Event detail modal */}
      {modalEvent && <EventModal event={modalEvent} onClose={() => setModalEvent(null)} />}
    </div>
  )
}

export default App
