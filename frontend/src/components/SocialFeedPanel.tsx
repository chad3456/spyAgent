import React, { useState } from 'react'
import { ExternalLink, CheckCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import type { SocialFeedsResponse, SocialFeedItem } from '../types/osint'
import clsx from 'clsx'

interface SocialFeedPanelProps {
  data: SocialFeedsResponse | null
  loading: boolean
}

const TOPIC_COLORS: Record<string, string> = {
  war: '#ff2d55',
  conflict: '#ff6b35',
  military: '#ff9f0a',
  geopolitics: '#ffd60a',
  defense: '#bf5af2',
  nato: '#5ac8fa',
  sanctions: '#30d158',
  diplomacy: '#64d2ff',
}

const PLATFORM_ICONS: Record<string, string> = {
  twitter: '𝕏',
  news: '📰',
  rss: '📡',
}

function FeedCard({ item }: { item: SocialFeedItem }) {
  const timeAgo = (() => {
    try {
      return formatDistanceToNow(new Date(item.publishedAt), { addSuffix: true })
    } catch {
      return item.publishedAt
    }
  })()

  const topicColor = TOPIC_COLORS[item.topic?.toLowerCase()] ?? '#64d2ff'
  const platformIcon = PLATFORM_ICONS[item.platform] ?? '📡'

  return (
    <div className="px-4 py-3 border-b border-[#1e3a5f]/50 hover:bg-[#1e3a5f]/15 transition-colors">
      {/* Author row */}
      <div className="flex items-center gap-2 mb-1.5">
        <span className="text-sm">{platformIcon}</span>
        <span className="text-[#e8f0fe] text-xs font-bold">@{item.author}</span>
        {item.verified && (
          <CheckCircle className="w-3 h-3 text-[#5ac8fa] flex-shrink-0" />
        )}
        <span
          className="ml-auto text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded flex-shrink-0"
          style={{ backgroundColor: `${topicColor}22`, color: topicColor }}
        >
          {item.topic}
        </span>
      </div>

      {/* Content */}
      <p className="text-[#e8f0fe] text-xs leading-relaxed line-clamp-4">
        {item.content}
      </p>

      {/* Meta */}
      <div className="flex items-center gap-2 mt-1.5">
        <span className="text-[#8ba3c0]/60 text-[10px]">{timeAgo}</span>
        {item.location && (
          <span className="text-[#8ba3c0]/60 text-[10px]">• 📍 {item.location}</span>
        )}
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="ml-auto text-[#8ba3c0]/40 hover:text-[#64d2ff] transition-colors"
        >
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </div>
  )
}

export const SocialFeedPanel: React.FC<SocialFeedPanelProps> = ({ data, loading }) => {
  const [activeTopic, setActiveTopic] = useState<string>('all')

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="w-6 h-6 border-2 border-[#5ac8fa] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!data) return null

  const topics = ['all', ...Object.keys(data.summary?.topics ?? {})]
  const feeds =
    activeTopic === 'all'
      ? data.feeds ?? []
      : data.feeds?.filter((f) => f.topic?.toLowerCase() === activeTopic) ?? []

  return (
    <div className="flex flex-col h-full">
      {/* Topic filter */}
      <div className="flex gap-1 px-3 py-2 border-b border-[#1e3a5f] overflow-x-auto flex-shrink-0">
        {topics.map((topic) => {
          const color = TOPIC_COLORS[topic] ?? '#5ac8fa'
          const isActive = activeTopic === topic
          const count = topic === 'all' ? data.feeds?.length : data.summary?.topics?.[topic]
          return (
            <button
              key={topic}
              onClick={() => setActiveTopic(topic)}
              className={clsx(
                'flex-shrink-0 text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded transition-all flex items-center gap-1'
              )}
              style={{
                backgroundColor: isActive ? `${color}22` : 'transparent',
                color: isActive ? color : '#8ba3c0',
                border: `1px solid ${isActive ? color : 'transparent'}`,
              }}
            >
              {topic}
              {count != null && (
                <span className="text-[8px] opacity-70">{count}</span>
              )}
            </button>
          )
        })}
      </div>

      {/* Legend */}
      <div className="px-4 py-1.5 border-b border-[#1e3a5f]/50 flex-shrink-0">
        <div className="flex items-center gap-3 text-[9px] text-[#8ba3c0]/60">
          <span>𝕏 Twitter/X</span>
          <span>📰 News</span>
          <span>📡 RSS</span>
          <CheckCircle className="w-2.5 h-2.5 text-[#5ac8fa]" />
          <span>Verified</span>
        </div>
      </div>

      {/* Feed items */}
      <div className="flex-1 overflow-y-auto">
        {feeds.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 gap-2">
            <span className="text-[#8ba3c0] text-xs">No feeds available</span>
            <span className="text-[#8ba3c0]/60 text-[10px]">Enable Social Feeds layer to load data</span>
          </div>
        ) : (
          feeds.map((item) => <FeedCard key={item.id} item={item} />)
        )}
      </div>
    </div>
  )
}
