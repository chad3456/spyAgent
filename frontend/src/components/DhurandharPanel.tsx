import React, { useState } from 'react'
import { X, Flame, WifiOff, Anchor, Rocket, Video, Radio } from 'lucide-react'
import clsx from 'clsx'
import {
  useFires,
  useInternetOutages,
  useSubmarines,
  useDrones,
  useCCTV,
  useSalvo,
} from '../hooks/useOSINTLayers'
import type {
  FireDetection,
  OutageEvent,
  SubmarineBase,
  SubmarineSighting,
  DroneIncident,
  DroneHotspot,
  PublicCamera,
  SalvoEvent,
  SalvoAnchor,
} from '../types/osint'

interface NewsItem { title: string; url: string; source: string; publishedAt: string }

type TabKey = 'salvo' | 'fires' | 'outages' | 'submarines' | 'drones' | 'cctv'

interface DhurandharPanelProps {
  open: boolean
  onClose: () => void
}

const TABS: { key: TabKey; label: string; icon: React.ReactNode; color: string }[] = [
  { key: 'salvo',      label: 'Iran/US Salvo',  icon: <Rocket  className="w-3.5 h-3.5" />, color: '#ff375f' },
  { key: 'fires',      label: 'Wildfires',      icon: <Flame   className="w-3.5 h-3.5" />, color: '#ff6a00' },
  { key: 'outages',    label: 'Outages',        icon: <WifiOff className="w-3.5 h-3.5" />, color: '#5e5ce6' },
  { key: 'submarines', label: 'Submarines',     icon: <Anchor  className="w-3.5 h-3.5" />, color: '#0a84ff' },
  { key: 'drones',     label: 'Drones',         icon: <Radio   className="w-3.5 h-3.5" />, color: '#ff453a' },
  { key: 'cctv',       label: 'CCTV',           icon: <Video   className="w-3.5 h-3.5" />, color: '#32d74b' },
]

const SectionTitle: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <h3 className="text-[10px] uppercase tracking-[0.18em] text-[#64d2ff] font-bold mb-2">{children}</h3>
)

const ItemCard: React.FC<{
  title: string
  meta?: string
  url?: string
  tag?: string
  tagColor?: string
}> = ({ title, meta, url, tag, tagColor }) => (
  <a
    href={url || '#'}
    target={url ? '_blank' : undefined}
    rel="noopener noreferrer"
    className="block bg-[#0a0f1e]/80 hover:bg-[#1e3a5f]/40 border border-[#1e3a5f] rounded-md px-3 py-2 transition-colors"
  >
    <div className="flex items-start gap-2">
      {tag && (
        <span
          className="text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider mt-0.5"
          style={{ backgroundColor: `${tagColor || '#64d2ff'}22`, color: tagColor || '#64d2ff' }}
        >
          {tag}
        </span>
      )}
      <div className="flex-1 min-w-0">
        <div className="text-[12px] text-[#e8f0fe] leading-snug line-clamp-2">{title}</div>
        {meta && <div className="text-[10px] text-[#8ba3c0] mt-1 truncate">{meta}</div>}
      </div>
    </div>
  </a>
)

export const DhurandharPanel: React.FC<DhurandharPanelProps> = ({ open, onClose }) => {
  const [tab, setTab] = useState<TabKey>('salvo')

  // Lazy-fetch: only call the hooks for tabs the user actually opens.
  const salvo  = useSalvo(open && tab === 'salvo')
  const fires  = useFires(open && tab === 'fires')
  const outages = useInternetOutages(open && tab === 'outages')
  const subs   = useSubmarines(open && tab === 'submarines')
  const drones = useDrones(open && tab === 'drones')
  const cctv   = useCCTV(open && tab === 'cctv')

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[2000] flex justify-end">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="relative w-full max-w-2xl h-full bg-[#0a0f1e] border-l border-[#1e3a5f] shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[#1e3a5f] bg-gradient-to-r from-[#1e3a5f]/60 to-transparent">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-red-600 to-orange-500 flex items-center justify-center">
            <Rocket className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1">
            <h2 className="text-[#e8f0fe] font-bold text-sm leading-tight">Dhurandhar Intel</h2>
            <p className="text-[#8ba3c0] text-[10px] leading-tight">
              Extended OSINT layers — salvo, fires, outages, subs, drones, CCTV
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-[#1e3a5f]/60 text-[#8ba3c0] hover:text-[#e8f0fe]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-[#1e3a5f] overflow-x-auto flex-shrink-0">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-2 text-[11px] font-medium border-b-2 transition-all flex-shrink-0',
                tab === t.key
                  ? 'border-current'
                  : 'border-transparent text-[#8ba3c0] hover:text-[#e8f0fe]'
              )}
              style={tab === t.key ? { color: t.color } : undefined}
            >
              {t.icon}
              {t.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {tab === 'salvo' && (
            <>
              {salvo.isLoading && <Loading label="Fetching salvo data…" />}
              {salvo.data && (
                <>
                  <Summary
                    items={[
                      { label: 'Total events', value: salvo.data.summary.totalEvents },
                      { label: 'Anchor exchanges', value: salvo.data.summary.anchorEvents },
                      { label: 'Critical anchors', value: salvo.data.summary.criticalAnchors },
                    ]}
                  />

                  <section>
                    <SectionTitle>Documented salvo anchors</SectionTitle>
                    <div className="space-y-2">
                      {salvo.data.anchors.map((a: SalvoAnchor) => (
                        <div key={a.id} className="bg-[#0a0f1e]/80 border border-[#1e3a5f] rounded-md p-3">
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <div className="text-[12px] font-semibold text-[#e8f0fe]">{a.name}</div>
                            <span
                              className="text-[9px] font-bold px-1.5 py-0.5 rounded uppercase"
                              style={{
                                background: a.severity === 'CRITICAL' ? '#ff375f22' : '#ff9f0a22',
                                color:      a.severity === 'CRITICAL' ? '#ff375f'   : '#ff9f0a',
                              }}
                            >
                              {a.severity}
                            </span>
                          </div>
                          <div className="text-[10px] text-[#8ba3c0] mb-1">{a.date} • {a.actor}</div>
                          <div className="text-[11px] text-[#e8f0fe]/90">
                            <span className="text-[#64d2ff]">{a.origin.name}</span> → <span className="text-[#ff453a]">{a.target.name}</span>
                          </div>
                          <div className="text-[11px] text-[#8ba3c0] mt-1">{a.munitions}</div>
                          <div className="text-[10px] mt-1.5">
                            <span className={clsx(
                              'px-1.5 py-0.5 rounded font-bold uppercase tracking-wider',
                              a.intercepted ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400',
                            )}>
                              {a.intercepted ? 'mostly intercepted' : 'impact'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>

                  <section>
                    <SectionTitle>Live salvo / strike events</SectionTitle>
                    <div className="space-y-1.5">
                      {salvo.data.events.slice(0, 25).map((e: SalvoEvent) => (
                        <ItemCard
                          key={e.id}
                          title={e.title}
                          meta={`${e.region || 'unknown'} • ${e.source} • ${e.publishedAt}`}
                          url={e.url}
                          tag={e.severity}
                          tagColor={e.severity === 'HIGH' ? '#ff375f' : '#ff9f0a'}
                        />
                      ))}
                    </div>
                  </section>
                </>
              )}
            </>
          )}

          {tab === 'fires' && (
            <>
              {fires.isLoading && <Loading label="Fetching NASA FIRMS detections…" />}
              {fires.data && (
                <>
                  <Summary
                    items={[
                      { label: 'Active fires (24 h)', value: fires.data.summary.total },
                      { label: 'Critical FRP', value: fires.data.summary.critical },
                      { label: 'High FRP', value: fires.data.summary.high },
                    ]}
                  />
                  <p className="text-[10px] text-[#8ba3c0]">Source: {fires.data.source}</p>

                  <section>
                    <SectionTitle>Hottest detections</SectionTitle>
                    <div className="grid grid-cols-2 gap-2">
                      {fires.data.fires.slice(0, 30).map((f: FireDetection) => (
                        <div key={f.id} className="bg-[#0a0f1e]/80 border border-[#1e3a5f] rounded p-2">
                          <div className="text-[11px] text-[#ff6a00] font-bold">FRP {f.frp} MW</div>
                          <div className="text-[10px] text-[#8ba3c0]">{f.lat.toFixed(2)}, {f.lon.toFixed(2)}</div>
                          <div className="text-[10px] text-[#8ba3c0]">{f.sensor} • {f.dayNight}</div>
                        </div>
                      ))}
                    </div>
                  </section>

                  {fires.data.news.length > 0 && (
                    <section>
                      <SectionTitle>Wildfire news</SectionTitle>
                      <div className="space-y-1.5">
                        {fires.data.news.map((n: NewsItem) => (
                          <ItemCard key={n.url} title={n.title} meta={`${n.source} • ${n.publishedAt}`} url={n.url} />
                        ))}
                      </div>
                    </section>
                  )}
                </>
              )}
            </>
          )}

          {tab === 'outages' && (
            <>
              {outages.isLoading && <Loading label="Fetching outage reports…" />}
              {outages.data && (
                <>
                  <Summary
                    items={[
                      { label: 'Reports', value: outages.data.summary.total },
                      { label: 'Active', value: outages.data.summary.active },
                      { label: 'Countries', value: outages.data.summary.countries },
                    ]}
                  />
                  <p className="text-[10px] text-[#8ba3c0]">
                    Sources: {outages.data.sources.join(', ') || 'none'} {outages.data.hasCFToken ? '' : '• CF_RADAR_TOKEN not set'}
                  </p>
                  <section>
                    <SectionTitle>Recent outages</SectionTitle>
                    <div className="space-y-1.5">
                      {outages.data.outages.map((o: OutageEvent) => (
                        <ItemCard
                          key={o.id}
                          title={o.title}
                          meta={`${o.country || o.countryCode || 'unknown'} • ${o.source} • ${o.reportedAt}`}
                          url={o.url}
                          tag={o.type}
                          tagColor={o.type === 'active' ? '#ff453a' : o.type === 'resolved' ? '#32d74b' : '#5e5ce6'}
                        />
                      ))}
                    </div>
                  </section>
                </>
              )}
            </>
          )}

          {tab === 'submarines' && (
            <>
              {subs.isLoading && <Loading label="Fetching submarine OSINT…" />}
              {subs.data && (
                <>
                  <Summary
                    items={[
                      { label: 'Bases', value: subs.data.summary.totalBases },
                      { label: 'Countries', value: subs.data.summary.countries },
                      { label: 'SSBN bases', value: subs.data.summary.ssbnBases },
                    ]}
                  />
                  <p className="text-[10px] text-[#8ba3c0] italic">{subs.data.disclaimer}</p>

                  <section>
                    <SectionTitle>Known submarine bases</SectionTitle>
                    <div className="grid grid-cols-2 gap-2">
                      {subs.data.bases.map((b: SubmarineBase) => (
                        <div key={b.name} className="bg-[#0a0f1e]/80 border border-[#1e3a5f] rounded p-2">
                          <div className="flex items-center justify-between">
                            <div className="text-[11px] text-[#e8f0fe] font-semibold leading-tight">{b.name}</div>
                            <span className="text-[9px] font-bold text-[#0a84ff]">{b.type}</span>
                          </div>
                          <div className="text-[10px] text-[#8ba3c0] mt-1">{b.country} • {b.fleet}</div>
                          <div className="text-[10px] text-[#64d2ff] mt-1">{b.lat.toFixed(2)}, {b.lon.toFixed(2)}</div>
                        </div>
                      ))}
                    </div>
                  </section>

                  {subs.data.sightings.length > 0 && (
                    <section>
                      <SectionTitle>OSINT sightings / deployments</SectionTitle>
                      <div className="space-y-1.5">
                        {subs.data.sightings.map((s: SubmarineSighting) => (
                          <ItemCard key={s.id} title={s.title} meta={`${s.source} • ${s.publishedAt}`} url={s.url} />
                        ))}
                      </div>
                    </section>
                  )}
                </>
              )}
            </>
          )}

          {tab === 'drones' && (
            <>
              {drones.isLoading && <Loading label="Fetching drone activity…" />}
              {drones.data && (
                <>
                  <Summary
                    items={[
                      { label: 'Incidents', value: drones.data.summary.totalIncidents },
                      { label: 'Hotspots', value: drones.data.summary.hotspotCount },
                      { label: 'High severity', value: drones.data.summary.highSeverity },
                    ]}
                  />

                  <section>
                    <SectionTitle>Drone hotspots</SectionTitle>
                    <div className="grid grid-cols-2 gap-2">
                      {drones.data.hotspots.map((h: DroneHotspot) => (
                        <div key={h.name} className="bg-[#0a0f1e]/80 border border-[#1e3a5f] rounded p-2">
                          <div className="text-[11px] text-[#e8f0fe] font-semibold">{h.name}</div>
                          <div className="text-[10px] text-[#8ba3c0]">{h.tag}</div>
                          <div className="text-[10px] text-[#ff453a] mt-1">{h.lat.toFixed(2)}, {h.lon.toFixed(2)}</div>
                        </div>
                      ))}
                    </div>
                  </section>

                  <section>
                    <SectionTitle>Recent drone incidents</SectionTitle>
                    <div className="space-y-1.5">
                      {drones.data.incidents.slice(0, 25).map((i: DroneIncident) => (
                        <ItemCard
                          key={i.id}
                          title={i.title}
                          meta={`${i.region} • ${i.source} • ${i.publishedAt}`}
                          url={i.url}
                          tag={i.severity}
                          tagColor={i.severity === 'HIGH' ? '#ff375f' : '#ff9f0a'}
                        />
                      ))}
                    </div>
                  </section>
                </>
              )}
            </>
          )}

          {tab === 'cctv' && (
            <>
              {cctv.isLoading && <Loading label="Loading public CCTV catalogue…" />}
              {cctv.data && (
                <>
                  <Summary
                    items={[
                      { label: 'Cameras', value: cctv.data.summary.total },
                      { label: 'Categories', value: Object.keys(cctv.data.summary.byCategory).length },
                      { label: 'Countries', value: Object.keys(cctv.data.summary.byCountry).length },
                    ]}
                  />
                  <p className="text-[10px] text-[#8ba3c0] italic">{cctv.data.disclaimer}</p>

                  <section>
                    <SectionTitle>Public live cameras</SectionTitle>
                    <div className="grid grid-cols-2 gap-2">
                      {cctv.data.cameras.map((c: PublicCamera) => (
                        <a
                          key={c.id}
                          href={c.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block bg-[#0a0f1e]/80 hover:bg-[#1e3a5f]/30 border border-[#1e3a5f] rounded p-2"
                        >
                          <div className="flex items-center justify-between">
                            <div className="text-[11px] text-[#e8f0fe] font-semibold leading-tight">{c.name}</div>
                            <span className="text-[9px] font-bold text-[#32d74b] uppercase">{c.category}</span>
                          </div>
                          <div className="text-[10px] text-[#8ba3c0] mt-1">{c.country} • {c.operator}</div>
                          <div className="text-[10px] text-[#64d2ff] mt-1">{c.lat.toFixed(2)}, {c.lon.toFixed(2)}</div>
                        </a>
                      ))}
                    </div>
                  </section>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

const Loading: React.FC<{ label: string }> = ({ label }) => (
  <div className="flex items-center gap-2 text-[#8ba3c0] text-[12px]">
    <div className="w-3 h-3 border-2 border-[#64d2ff] border-t-transparent rounded-full animate-spin" />
    {label}
  </div>
)

const Summary: React.FC<{ items: { label: string; value: number | string }[] }> = ({ items }) => (
  <div className="grid grid-cols-3 gap-2">
    {items.map((s) => (
      <div key={s.label} className="bg-[#1e3a5f]/30 border border-[#1e3a5f] rounded p-2 text-center">
        <div className="text-[16px] font-bold text-[#e8f0fe]">{s.value}</div>
        <div className="text-[9px] text-[#8ba3c0] uppercase tracking-wider mt-0.5">{s.label}</div>
      </div>
    ))}
  </div>
)
