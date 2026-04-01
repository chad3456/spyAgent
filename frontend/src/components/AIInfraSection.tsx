import React, { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, AlertCircle, RefreshCw, X, Cpu, Building2, Rocket, TrendingUp } from 'lucide-react'
import clsx from 'clsx'
import { fetchAIInfraData } from '../api/client'
import type { NewsItem } from '../types'
import NewsCard from './NewsCard'
import { SectionSkeleton } from './LoadingSkeleton'

// ─── Category config ─────────────────────────────────────────────────────────

interface CategoryConfig {
  label: string
  icon: React.FC<{ className?: string }>
  color: string
  activeClass: string
  keywords: string[]
}

const CATEGORIES: CategoryConfig[] = [
  {
    label: 'All',
    icon: ({ className }) => <span className={className}>✦</span>,
    color: 'text-[#8ba3c0]',
    activeClass: 'bg-[#FF9933]/20 text-[#FF9933] border-[#FF9933]/40',
    keywords: [],
  },
  {
    label: 'AI',
    icon: Cpu,
    color: 'text-purple-400',
    activeClass: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
    keywords: ['artificial intelligence', 'ai ', 'machine learning', 'ml ', 'deep learning', 'llm', 'chatbot', 'openai', 'google ai', 'nvidia', 'generative'],
  },
  {
    label: 'Data Centers',
    icon: Building2,
    color: 'text-blue-400',
    activeClass: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
    keywords: ['data center', 'datacenter', 'cloud', 'aws', 'azure', 'hyperscale', 'server farm', 'colocation'],
  },
  {
    label: 'Startups',
    icon: Rocket,
    color: 'text-emerald-400',
    activeClass: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
    keywords: ['startup', 'unicorn', 'seed', 'series a', 'series b', 'founder', 'venture', 'incubator', 'accelerator'],
  },
  {
    label: 'Investment',
    icon: TrendingUp,
    color: 'text-[#FF9933]',
    activeClass: 'bg-[#FF9933]/20 text-[#FF9933] border-[#FF9933]/40',
    keywords: ['investment', 'funding', 'billion', 'crore', 'vc ', 'private equity', 'ipo', 'fund'],
  },
]

function matchesCategory(item: NewsItem, category: CategoryConfig): boolean {
  if (category.label === 'All') return true
  const text = (item.title + ' ' + (item.category ?? '') + ' ' + item.source).toLowerCase()
  if (item.category) {
    const catLower = item.category.toLowerCase()
    if (catLower.includes(category.label.toLowerCase())) return true
  }
  return category.keywords.some((kw) => text.includes(kw))
}

// ─── Error state ─────────────────────────────────────────────────────────────

const ErrorState: React.FC<{ message: string; onRetry: () => void }> = ({
  message,
  onRetry,
}) => (
  <div className="flex flex-col items-center justify-center py-16 gap-4">
    <AlertCircle className="w-12 h-12 text-red-400" />
    <div className="text-center">
      <p className="text-[#e8f0fe] font-semibold mb-1">Failed to load AI & Tech data</p>
      <p className="text-[#8ba3c0] text-sm">{message}</p>
    </div>
    <button
      onClick={onRetry}
      className="flex items-center gap-2 px-4 py-2 bg-[#FF9933]/20 text-[#FF9933] border border-[#FF9933]/40 rounded-lg hover:bg-[#FF9933]/30 transition-colors text-sm font-medium"
    >
      <RefreshCw className="w-4 h-4" />
      Retry
    </button>
  </div>
)

// ─── Stats bar ───────────────────────────────────────────────────────────────

const StatsBar: React.FC<{ news: NewsItem[] }> = ({ news }) => {
  const counts = CATEGORIES.slice(1).map((cat) => ({
    label: cat.label,
    count: news.filter((item) => matchesCategory(item, cat)).length,
    color: cat.color,
    Icon: cat.icon,
  }))

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {counts.map((c) => (
        <div key={c.label} className="card flex items-center gap-3">
          <div className="p-2 bg-[#1e3a5f]/40 rounded-lg">
            <c.Icon className={clsx('w-4 h-4', c.color)} />
          </div>
          <div>
            <p className="text-[#e8f0fe] font-bold text-lg metric-value">{c.count}</p>
            <p className="text-[#8ba3c0] text-xs">{c.label} stories</p>
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── Main component ──────────────────────────────────────────────────────────

const AIInfraSection: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState('All')
  const [searchQuery, setSearchQuery] = useState('')

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['ai-infra'],
    queryFn: fetchAIInfraData,
    refetchInterval: 5 * 60 * 1000,
    staleTime: 5 * 60 * 1000,
  })

  const filteredNews = useMemo(() => {
    if (!data?.news) return []
    let items = data.news

    // Category filter
    const cat = CATEGORIES.find((c) => c.label === activeCategory)
    if (cat && cat.label !== 'All') {
      items = items.filter((item) => matchesCategory(item, cat))
    }

    // Search filter
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase()
      items = items.filter(
        (item) =>
          item.title.toLowerCase().includes(q) ||
          item.source.toLowerCase().includes(q) ||
          (item.category ?? '').toLowerCase().includes(q)
      )
    }

    return items
  }, [data?.news, activeCategory, searchQuery])

  if (isLoading) return <SectionSkeleton />
  if (isError) {
    const msg = error instanceof Error ? error.message : 'Unknown error'
    return <ErrorState message={msg} onRetry={() => refetch()} />
  }
  if (!data) return null

  return (
    <div className="space-y-6">
      {/* Stats bar */}
      <StatsBar news={data.news ?? []} />

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
        {/* Category filter */}
        <div className="flex items-center gap-2 flex-wrap">
          {CATEGORIES.map((cat) => {
            const isActive = activeCategory === cat.label
            const Icon = cat.icon
            return (
              <button
                key={cat.label}
                onClick={() => setActiveCategory(cat.label)}
                className={clsx(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all duration-150',
                  isActive
                    ? cat.activeClass
                    : 'bg-transparent border-[#1e3a5f] text-[#8ba3c0] hover:border-[#2a5080] hover:text-[#e8f0fe]'
                )}
              >
                <Icon className="w-3 h-3" />
                {cat.label}
              </button>
            )
          })}
        </div>

        {/* Search */}
        <div className="relative flex-shrink-0 w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#8ba3c0]" />
          <input
            type="text"
            placeholder="Search news…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#0d1b2e] border border-[#1e3a5f] rounded-lg pl-8 pr-8 py-1.5 text-xs text-[#e8f0fe] placeholder-[#8ba3c0] focus:outline-none focus:border-[#FF9933]/60 transition-colors"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8ba3c0] hover:text-[#e8f0fe]"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Result count */}
      <p className="text-[#8ba3c0] text-xs">
        {filteredNews.length} {filteredNews.length === 1 ? 'story' : 'stories'} found
        {activeCategory !== 'All' && ` in ${activeCategory}`}
        {searchQuery && ` matching "${searchQuery}"`}
      </p>

      {/* News grid */}
      {filteredNews.length > 0 ? (
        <div className="columns-1 sm:columns-2 xl:columns-3 gap-4 space-y-4">
          {filteredNews.map((item, i) => (
            <div key={i} className="break-inside-avoid mb-4">
              <NewsCard item={item} />
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-16">
          <Search className="w-10 h-10 text-[#1e3a5f] mx-auto mb-3" />
          <p className="text-[#e8f0fe] font-medium">No stories found</p>
          <p className="text-[#8ba3c0] text-sm mt-1">
            Try a different filter or search term
          </p>
          {(activeCategory !== 'All' || searchQuery) && (
            <button
              onClick={() => { setActiveCategory('All'); setSearchQuery('') }}
              className="mt-4 px-4 py-2 bg-[#1e3a5f]/60 text-[#8ba3c0] rounded-lg text-sm hover:text-[#e8f0fe] transition-colors"
            >
              Clear filters
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default AIInfraSection
