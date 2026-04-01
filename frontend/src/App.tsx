import React, { useState, Suspense, lazy } from 'react'
import { RefreshCw, Wifi, WifiOff, Clock } from 'lucide-react'
import clsx from 'clsx'
import { format, parseISO, isValid } from 'date-fns'
import type { TabId } from './types'
import { SectionSkeleton } from './components/LoadingSkeleton'

// Lazy-load heavy sections for fast initial render
const EconomicSection = lazy(() => import('./components/EconomicSection'))
const AIInfraSection = lazy(() => import('./components/AIInfraSection'))
const InfraSection = lazy(() => import('./components/InfraSection'))
const DefenseSection = lazy(() => import('./components/DefenseSection'))

// ─── Tab config ───────────────────────────────────────────────────────────────

interface TabConfig {
  id: TabId
  label: string
  emoji: string
  description: string
}

const TABS: TabConfig[] = [
  {
    id: 'economy',
    label: 'Economy',
    emoji: '📈',
    description: 'GDP · FDI · Inflation · Trade',
  },
  {
    id: 'ai-tech',
    label: 'AI & Tech',
    emoji: '🤖',
    description: 'AI · Data Centers · Startups',
  },
  {
    id: 'infrastructure',
    label: 'Infrastructure',
    emoji: '⚡',
    description: 'Roads · Power · Energy',
  },
  {
    id: 'defence',
    label: 'Defence',
    emoji: '🛡️',
    description: 'Military · SIPRI · Procurement',
  },
]

// ─── Tricolor header bar ──────────────────────────────────────────────────────

const TricolorBar: React.FC = () => (
  <div className="h-1 w-full flex">
    <div className="flex-1 bg-[#FF9933]" />
    <div className="flex-1 bg-white/90" />
    <div className="flex-1 bg-[#138808]" />
  </div>
)

// ─── Status indicator ─────────────────────────────────────────────────────────

const StatusIndicator: React.FC<{ online: boolean }> = ({ online }) => (
  <div className="flex items-center gap-1.5 text-xs">
    {online ? (
      <>
        <Wifi className="w-3.5 h-3.5 text-emerald-400" />
        <span className="text-emerald-400">Live</span>
      </>
    ) : (
      <>
        <WifiOff className="w-3.5 h-3.5 text-red-400" />
        <span className="text-red-400">Offline</span>
      </>
    )}
  </div>
)

// ─── Last updated display ─────────────────────────────────────────────────────

function formatLastUpdated(iso: string | undefined): string {
  if (!iso) return '—'
  try {
    const date = parseISO(iso)
    if (!isValid(date)) return iso
    return format(date, 'dd MMM yyyy, HH:mm z')
  } catch {
    return iso
  }
}

// ─── Health check (ping /api/economic to determine connectivity) ──────────────

function useHealthCheck() {
  // We use a lightweight check via the React Query cache — if any query
  // succeeds we're "online"; we don't make a separate request.
  const [online, setOnline] = React.useState(true)

  React.useEffect(() => {
    const handler = () => setOnline(navigator.onLine)
    window.addEventListener('online', handler)
    window.addEventListener('offline', handler)
    setOnline(navigator.onLine)
    return () => {
      window.removeEventListener('online', handler)
      window.removeEventListener('offline', handler)
    }
  }, [])

  return online
}

// ─── Main App ─────────────────────────────────────────────────────────────────

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('economy')
  const online = useHealthCheck()

  const [lastUpdated] = React.useState<string | null>(null)

  // Global manual refresh — refetch all active queries by invalidating
  const handleRefresh = React.useCallback(() => {
    // Each section handles its own refetch via React Query.
    // We trigger a full page reload of data by bumping a key.
    window.location.reload()
  }, [])

  return (
    <div className="min-h-screen bg-[#0a0f1e] text-[#e8f0fe]">
      {/* Top tricolor stripe */}
      <TricolorBar />

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-[#0a0f1e]/95 backdrop-blur-sm border-b border-[#1e3a5f]">
        <div className="max-w-screen-xl mx-auto px-4 sm:px-6 py-3">
          <div className="flex items-center justify-between gap-4">
            {/* Brand */}
            <div className="flex items-center gap-3 min-w-0">
              <span className="text-3xl leading-none select-none">🇮🇳</span>
              <div className="min-w-0">
                <h1 className="text-[#e8f0fe] font-bold text-lg sm:text-xl leading-tight truncate">
                  India Progress Dashboard
                </h1>
                <p className="text-[#8ba3c0] text-[11px] hidden sm:block mt-0.5">
                  Live Tracker — Economic · Technology · Infrastructure · Defence
                </p>
              </div>
            </div>

            {/* Right side */}
            <div className="flex items-center gap-3 flex-shrink-0">
              <StatusIndicator online={online} />
              {lastUpdated && (
                <div className="hidden md:flex items-center gap-1.5 text-[#8ba3c0] text-[11px]">
                  <Clock className="w-3 h-3" />
                  <span>Updated {formatLastUpdated(lastUpdated)}</span>
                </div>
              )}
              <button
                onClick={handleRefresh}
                title="Refresh all data"
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1e3a5f]/60 hover:bg-[#1e3a5f] border border-[#1e3a5f] rounded-lg text-[#8ba3c0] hover:text-[#e8f0fe] transition-all text-xs"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Refresh</span>
              </button>
            </div>
          </div>

          {/* ── Tabs ──────────────────────────────────────────────────────── */}
          <nav className="flex items-center gap-0 mt-3 -mb-px overflow-x-auto no-scrollbar">
            {TABS.map((tab) => {
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={clsx(
                    'flex items-center gap-2 px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-all duration-150 flex-shrink-0',
                    isActive
                      ? 'border-[#FF9933] text-[#FF9933]'
                      : 'border-transparent text-[#8ba3c0] hover:text-[#e8f0fe] hover:border-[#1e3a5f]'
                  )}
                >
                  <span className="text-base leading-none">{tab.emoji}</span>
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>
      </header>

      {/* ── Breadcrumb / section description ───────────────────────────────── */}
      <div className="max-w-screen-xl mx-auto px-4 sm:px-6 py-3 border-b border-[#1e3a5f]/40">
        <p className="text-[#8ba3c0] text-xs">
          {TABS.find((t) => t.id === activeTab)?.description ?? ''}
        </p>
      </div>

      {/* ── Main content ───────────────────────────────────────────────────── */}
      <main className="max-w-screen-xl mx-auto px-4 sm:px-6 py-6">
        <Suspense fallback={<SectionSkeleton />}>
          {activeTab === 'economy' && (
            <EconomicSection key="economy" />
          )}
          {activeTab === 'ai-tech' && (
            <AIInfraSection key="ai-tech" />
          )}
          {activeTab === 'infrastructure' && (
            <InfraSection key="infrastructure" />
          )}
          {activeTab === 'defence' && (
            <DefenseSection key="defence" />
          )}
        </Suspense>
      </main>

      {/* ── Footer ──────────────────────────────────────────────────────────── */}
      <footer className="border-t border-[#1e3a5f] mt-12 py-6">
        <div className="max-w-screen-xl mx-auto px-4 sm:px-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-[#8ba3c0] text-xs">
              <span>🇮🇳</span>
              <span>India Progress Dashboard</span>
              <span className="text-[#1e3a5f]">·</span>
              <span>Data auto-refreshes every 5 minutes</span>
            </div>
            <div className="flex items-center gap-3 text-[#8ba3c0] text-xs">
              <span>Sources: World Bank · SIPRI · NewsAPI</span>
            </div>
          </div>
          <TricolorBar />
        </div>
      </footer>
    </div>
  )
}

export default App
