import React, { useState, useMemo } from 'react'
import { Globe3D } from './Globe3D'
import { GlobePointModal } from './GlobePointModal'
import { NewsIntelPanel } from './NewsIntelPanel'
import { SocialFeedPanel } from './SocialFeedPanel'
import type { GlobePoint, LayerKey } from '../types/osint'
import type {
  Aircraft,
  MilitaryAircraft,
  Vessel,
  Earthquake,
  DDoSCountry,
  Satellite,
  HealthOutbreak,
  DatacenterFacility,
  SocialFeedsResponse,
  NewsIntelResponse,
} from '../types/osint'
import type { ProtestEvent, HAPIEvent } from '../types/protest'
import { Newspaper, Radio, X } from 'lucide-react'
import clsx from 'clsx'

interface OSINTGlobeProps {
  // Conflict data (always loaded)
  protests: ProtestEvent[]
  hapiEvents: HAPIEvent[]
  // Active layer set (owned by App)
  activeLayers: Set<LayerKey>
  loadingLayers: Set<LayerKey>
  // Per-layer data (passed from App)
  flights: Aircraft[]
  militaryFlights: MilitaryAircraft[]
  vessels: Vessel[]
  earthquakes: Earthquake[]
  ddos: DDoSCountry[]
  satellites: Satellite[]
  healthOutbreaks: HealthOutbreak[]
  datacenters: DatacenterFacility[]
  // Side panel data
  socialData: SocialFeedsResponse | null
  newsData: NewsIntelResponse | null
  socialLoading: boolean
  newsLoading: boolean
}

type SidePanel = 'news' | 'social' | null

export const OSINTGlobe: React.FC<OSINTGlobeProps> = ({
  protests,
  hapiEvents,
  activeLayers,
  flights,
  militaryFlights,
  vessels,
  earthquakes,
  ddos,
  satellites,
  healthOutbreaks,
  datacenters,
  socialData,
  newsData,
  socialLoading,
  newsLoading,
}) => {
  const [selectedPoint, setSelectedPoint] = useState<GlobePoint | null>(null)
  const [sidePanel, setSidePanel] = useState<SidePanel>(null)

  const allDatacenters = useMemo(() => datacenters, [datacenters])

  return (
    <div className="relative w-full h-full overflow-hidden bg-[#020810]">
      {/* Globe */}
      <Globe3D
        flights={flights}
        militaryFlights={militaryFlights}
        vessels={vessels}
        earthquakes={earthquakes}
        ddos={ddos}
        satellites={satellites}
        protests={protests}
        hapiEvents={hapiEvents}
        healthOutbreaks={healthOutbreaks}
        datacenters={allDatacenters}
        activeLayers={activeLayers}
        onPointClick={setSelectedPoint}
      />

      {/* Quick-access side panel buttons - bottom right */}
      <div className="absolute bottom-4 right-4 z-30 flex flex-col gap-2">
        <button
          onClick={() => setSidePanel(sidePanel === 'news' ? null : 'news')}
          className={clsx(
            'flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-all shadow-lg',
            sidePanel === 'news'
              ? 'bg-[#ffd60a]/20 border-[#ffd60a] text-[#ffd60a]'
              : 'bg-[#0d1b2e]/90 border-[#1e3a5f] text-[#8ba3c0] hover:text-[#e8f0fe]'
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
              : 'bg-[#0d1b2e]/90 border-[#1e3a5f] text-[#8ba3c0] hover:text-[#e8f0fe]'
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
      {sidePanel === 'news' && (
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
      {sidePanel === 'social' && (
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
