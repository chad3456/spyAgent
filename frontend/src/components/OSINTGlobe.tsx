import React, { useState, useCallback, useMemo } from 'react'
import { Globe3D } from './Globe3D'
import { LayerControl } from './LayerControl'
import { GlobePointModal } from './GlobePointModal'
import { NewsIntelPanel } from './NewsIntelPanel'
import { SocialFeedPanel } from './SocialFeedPanel'
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
} from '../hooks/useOSINTLayers'
import type { GlobePoint, LayerKey } from '../types/osint'
import type { ProtestEvent, HAPIEvent } from '../types/protest'
import { Newspaper, Radio, X } from 'lucide-react'
import clsx from 'clsx'

interface OSINTGlobeProps {
  protests: ProtestEvent[]
  hapiEvents: HAPIEvent[]
}

type SidePanel = 'news' | 'social' | null

export const OSINTGlobe: React.FC<OSINTGlobeProps> = ({ protests, hapiEvents }) => {
  const [activeLayers, setActiveLayers] = useState<Set<LayerKey>>(
    new Set<LayerKey>(['conflicts'])
  )
  const [selectedPoint, setSelectedPoint] = useState<GlobePoint | null>(null)
  const [sidePanel, setSidePanel] = useState<SidePanel>(null)

  // Layer toggle
  const handleToggleLayer = useCallback((key: LayerKey) => {
    setActiveLayers((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }, [])

  // Fetch each layer only when enabled
  const { data: flightsData, isLoading: flightsLoading } = useFlights(activeLayers.has('flights'))
  const { data: milData, isLoading: milLoading } = useMilitaryFlights(activeLayers.has('military_flights'))
  const { data: vesselData, isLoading: vesselLoading } = useVessels(activeLayers.has('vessels'))
  const { data: eqData, isLoading: eqLoading } = useEarthquakes(activeLayers.has('earthquakes'))
  const { data: ddosData, isLoading: ddosLoading } = useDDoS(activeLayers.has('ddos'))
  const { data: satData, isLoading: satLoading } = useSatellites(activeLayers.has('satellites'))
  const { data: healthData, isLoading: healthLoading } = useHealth(activeLayers.has('health'))
  const { data: dcData, isLoading: dcLoading } = useDatacenters(activeLayers.has('datacenters'))
  const { data: socialData, isLoading: socialLoading } = useSocialFeeds(activeLayers.has('social_feeds'))
  const { data: newsData, isLoading: newsLoading } = useNewsIntel(activeLayers.has('news_intel'))

  const loadingLayers = useMemo(() => {
    const loading = new Set<LayerKey>()
    if (flightsLoading && activeLayers.has('flights')) loading.add('flights')
    if (milLoading && activeLayers.has('military_flights')) loading.add('military_flights')
    if (vesselLoading && activeLayers.has('vessels')) loading.add('vessels')
    if (eqLoading && activeLayers.has('earthquakes')) loading.add('earthquakes')
    if (ddosLoading && activeLayers.has('ddos')) loading.add('ddos')
    if (satLoading && activeLayers.has('satellites')) loading.add('satellites')
    if (healthLoading && activeLayers.has('health')) loading.add('health')
    if (dcLoading && activeLayers.has('datacenters')) loading.add('datacenters')
    if (socialLoading && activeLayers.has('social_feeds')) loading.add('social_feeds')
    if (newsLoading && activeLayers.has('news_intel')) loading.add('news_intel')
    return loading
  }, [
    flightsLoading, milLoading, vesselLoading, eqLoading, ddosLoading,
    satLoading, healthLoading, dcLoading, socialLoading, newsLoading, activeLayers
  ])

  // Combine datacenters for globe
  const allDatacenters = useMemo(() => {
    if (!dcData) return []
    return [
      ...(dcData.datacenters ?? []),
      ...(dcData.cloudRegions ?? []),
      ...(dcData.internetExchanges ?? []),
    ]
  }, [dcData])

  return (
    <div className="relative w-full h-full overflow-hidden bg-[#020810]">
      {/* Globe */}
      <Globe3D
        flights={flightsData?.aircraft ?? []}
        militaryFlights={milData?.aircraft ?? []}
        vessels={vesselData?.vessels ?? []}
        earthquakes={eqData?.earthquakes ?? []}
        ddos={ddosData?.countries ?? []}
        satellites={satData?.satellites ?? []}
        protests={protests}
        hapiEvents={hapiEvents}
        healthOutbreaks={healthData?.outbreaks ?? []}
        datacenters={allDatacenters}
        activeLayers={activeLayers}
        onPointClick={setSelectedPoint}
      />

      {/* Layer control - top right */}
      <div className="absolute top-4 right-4 z-30">
        <LayerControl
          activeLayers={activeLayers}
          onToggleLayer={handleToggleLayer}
          loadingLayers={loadingLayers}
        />
      </div>

      {/* Quick-access side panel buttons - bottom right */}
      <div className="absolute bottom-4 right-4 z-30 flex flex-col gap-2">
        <button
          onClick={() => setSidePanel(sidePanel === 'news' ? null : 'news')}
          className={clsx(
            'flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-all shadow-lg',
            sidePanel === 'news'
              ? 'bg-[#ffd60a]/20 border-[#ffd60a] text-[#ffd60a]'
              : 'bg-[#0d1b2e]/90 border-[#1e3a5f] text-[#8ba3c0] hover:text-[#e8f0fe] hover:border-[#ffd60a]/50'
          )}
        >
          <Newspaper className="w-3.5 h-3.5" />
          Intel News
          {newsData?.summary?.totalArticles != null && (
            <span className="bg-[#ffd60a]/20 text-[#ffd60a] text-[9px] px-1 py-0.5 rounded-full font-bold">
              {newsData.summary.totalArticles}
            </span>
          )}
        </button>
        <button
          onClick={() => setSidePanel(sidePanel === 'social' ? null : 'social')}
          className={clsx(
            'flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-all shadow-lg',
            sidePanel === 'social'
              ? 'bg-[#5ac8fa]/20 border-[#5ac8fa] text-[#5ac8fa]'
              : 'bg-[#0d1b2e]/90 border-[#1e3a5f] text-[#8ba3c0] hover:text-[#e8f0fe] hover:border-[#5ac8fa]/50'
          )}
        >
          <Radio className="w-3.5 h-3.5" />
          OSINT Feeds
          {socialData?.summary?.totalPosts != null && (
            <span className="bg-[#5ac8fa]/20 text-[#5ac8fa] text-[9px] px-1 py-0.5 rounded-full font-bold">
              {socialData.summary.totalPosts}
            </span>
          )}
        </button>
      </div>

      {/* News panel */}
      {sidePanel === 'news' && newsData && (
        <div className="absolute bottom-0 right-0 top-0 z-30 w-80 xl:w-96">
          <div className="h-full bg-[#0d1b2e]/98 border-l border-[#1e3a5f] flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-[#1e3a5f]">
              <div className="flex items-center gap-2">
                <Newspaper className="w-4 h-4 text-[#ffd60a]" />
                <span className="text-[#e8f0fe] text-sm font-bold">Intelligence News</span>
              </div>
              <button onClick={() => setSidePanel(null)} className="text-[#8ba3c0] hover:text-[#e8f0fe]">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              <NewsIntelPanel data={newsData} loading={newsLoading} />
            </div>
          </div>
        </div>
      )}

      {/* Social feeds panel */}
      {sidePanel === 'social' && socialData && (
        <div className="absolute bottom-0 right-0 top-0 z-30 w-80 xl:w-96">
          <div className="h-full bg-[#0d1b2e]/98 border-l border-[#1e3a5f] flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-[#1e3a5f]">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-[#5ac8fa]" />
                <span className="text-[#e8f0fe] text-sm font-bold">OSINT Social Feeds</span>
              </div>
              <button onClick={() => setSidePanel(null)} className="text-[#8ba3c0] hover:text-[#e8f0fe]">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              <SocialFeedPanel data={socialData} loading={socialLoading} />
            </div>
          </div>
        </div>
      )}

      {/* Selected point modal */}
      {selectedPoint && (
        <GlobePointModal point={selectedPoint} onClose={() => setSelectedPoint(null)} />
      )}
    </div>
  )
}
