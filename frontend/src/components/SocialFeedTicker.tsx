import React, { useState, useEffect, useRef } from 'react'
import { Radio, ChevronUp, ChevronDown, ExternalLink, RefreshCw } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'
import type { SocialFeedsResponse, SocialFeedItem } from '../types/osint'

interface SocialFeedTickerProps {
  data: SocialFeedsResponse | null | undefined
  loading: boolean
}

const PLATFORM_ICONS: Record<string, string> = { twitter: '𝕏', news: '📰', rss: '📡' }
const TOPIC_COLORS: Record<string, string> = {
  war: '#ff2d55',
  conflict: '#ff6b35',
  military: '#ff9f0a',
  geopolitics: '#ffd60a',
  defense: '#bf5af2',
  nato: '#5ac8fa',
  sanctions: '#30d158',
  cyber: '#ff375f',
  diplomacy: '#64d2ff',
}

function TickerItem({ item }: { item: SocialFeedItem }) {
  const topicColor = TOPIC_COLORS[item.topic?.toLowerCase()] ?? '#64d2ff'
  const icon = PLATFORM_ICONS[item.platform] ?? '📡'
  const timeAgo = (() => {
    try { return formatDistanceToNow(new Date(item.publishedAt), { addSuffix: true }) }
    catch { return '' }
  })()

  return (
    <div className="flex items-start gap-2 px-4 py-2 border-b border-[#1e3a5f]/40 hover:bg-[#1e3a5f]/20 transition-colors group">
      <div className="flex items-center gap-1.5 flex-shrink-0 pt-0.5">
        <span className="text-sm">{icon}</span>
        <span
          className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded flex-shrink-0"
          style={{ backgroundColor: `${topicColor}22`, color: topicColor }}
        >
          {item.topic}
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-2">
          <span className="text-[#64d2ff] text-[11px] font-bold flex-shrink-0">@{item.author}</span>
          {item.verified && <span className="text-[#5ac8fa] text-[9px]">✓</span>}
          <span className="text-[#8ba3c0]/60 text-[10px] flex-shrink-0">{timeAgo}</span>
        </div>
        <p className="text-[#e8f0fe] text-[11px] leading-tight line-clamp-2 mt-0.5">{item.content}</p>
      </div>
      <a
        href={item.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-[#8ba3c0]/30 hover:text-[#64d2ff] transition-colors flex-shrink-0 pt-1"
        onClick={(e) => e.stopPropagation()}
      >
        <ExternalLink className="w-3 h-3" />
      </a>
    </div>
  )
}

export const SocialFeedTicker: React.FC<SocialFeedTickerProps> = ({ data, loading }) => {
  const [expanded, setExpanded] = useState(false)
  const [activeIndex, setActiveIndex] = useState(0)
  const tickerRef = useRef<HTMLDivElement>(null)

  const feeds = data?.feeds ?? []

  // Auto-advance the collapsed ticker every 5s
  useEffect(() => {
    if (expanded || feeds.length === 0) return
    const id = setInterval(() => {
      setActiveIndex((i) => (i + 1) % feeds.length)
    }, 5000)
    return () => clearInterval(id)
  }, [expanded, feeds.length])

  const currentItem = feeds[activeIndex]

  return (
    <div
      className={clsx(
        'flex-shrink-0 border-t border-[#1e3a5f] bg-[#060d1a]/98 backdrop-blur-sm transition-all duration-300 z-40',
        expanded ? 'h-56' : 'h-9'
      )}
    >
      {/* Ticker bar — always visible */}
      <div className="flex items-center h-9 px-3 gap-2 flex-shrink-0">
        {/* Label */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <Radio className="w-3 h-3 text-[#5ac8fa]" />
          <span className="text-[#5ac8fa] text-[10px] font-bold uppercase tracking-wider">OSINT Feed</span>
          {loading && <RefreshCw className="w-2.5 h-2.5 text-[#5ac8fa] animate-spin" />}
          {feeds.length > 0 && (
            <span className="bg-[#5ac8fa]/20 text-[#5ac8fa] text-[9px] px-1.5 py-0.5 rounded-full font-bold">
              {feeds.length}
            </span>
          )}
        </div>

        <div className="w-px h-4 bg-[#1e3a5f] flex-shrink-0" />

        {/* Scrolling item */}
        {currentItem ? (
          <div className="flex-1 min-w-0 flex items-center gap-2 overflow-hidden">
            <span className="text-[10px] flex-shrink-0">{PLATFORM_ICONS[currentItem.platform] ?? '📡'}</span>
            <span className="text-[#64d2ff] text-[10px] font-bold flex-shrink-0">@{currentItem.author}</span>
            {currentItem.verified && <span className="text-[#5ac8fa] text-[9px] flex-shrink-0">✓</span>}
            <span
              className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded flex-shrink-0"
              style={{
                backgroundColor: `${TOPIC_COLORS[currentItem.topic?.toLowerCase()] ?? '#64d2ff'}22`,
                color: TOPIC_COLORS[currentItem.topic?.toLowerCase()] ?? '#64d2ff',
              }}
            >
              {currentItem.topic}
            </span>
            <p className="text-[#e8f0fe] text-[10px] truncate flex-1 min-w-0">
              {currentItem.content}
            </p>
          </div>
        ) : (
          <span className="text-[#8ba3c0] text-[10px] flex-1">
            {loading ? 'Loading intelligence feeds…' : 'Enable Social Feeds layer to load geopolitical intelligence'}
          </span>
        )}

        {/* Controls */}
        <div className="flex items-center gap-1 flex-shrink-0 ml-2">
          {feeds.length > 1 && !expanded && (
            <span className="text-[#8ba3c0]/50 text-[9px]">{activeIndex + 1}/{feeds.length}</span>
          )}
          <button
            onClick={() => setExpanded((v) => !v)}
            className="text-[#8ba3c0] hover:text-[#5ac8fa] transition-colors p-0.5"
            title={expanded ? 'Collapse' : 'Expand feed'}
          >
            {expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Expanded panel */}
      {expanded && (
        <div
          ref={tickerRef}
          className="overflow-y-auto"
          style={{ height: 'calc(100% - 36px)' }}
        >
          {feeds.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-2 text-center px-4">
              <Radio className="w-6 h-6 text-[#8ba3c0]/40" />
              <p className="text-[#8ba3c0] text-xs">No feed data available</p>
              <p className="text-[#8ba3c0]/60 text-[10px]">Toggle "OSINT Social Feeds" layer to load live intelligence</p>
            </div>
          ) : (
            feeds.map((item) => <TickerItem key={item.id} item={item} />)
          )}
        </div>
      )}
    </div>
  )
}
