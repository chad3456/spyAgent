import React from 'react'
import { ExternalLink, Clock } from 'lucide-react'
import { formatDistanceToNow, parseISO, isValid } from 'date-fns'
import clsx from 'clsx'
import type { NewsItem } from '../types'

interface NewsCardProps {
  item: NewsItem
  compact?: boolean
}

const SOURCE_COLORS: Record<string, string> = {
  'Reuters': 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  'Bloomberg': 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  'Economic Times': 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  'Times of India': 'bg-red-500/20 text-red-300 border-red-500/30',
  'Mint': 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  'Hindu': 'bg-green-500/20 text-green-300 border-green-500/30',
  'Hindustan Times': 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
  'NDTV': 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  'Business Standard': 'bg-teal-500/20 text-teal-300 border-teal-500/30',
  'Financial Express': 'bg-pink-500/20 text-pink-300 border-pink-500/30',
  'default': 'bg-[#1e3a5f]/60 text-[#8ba3c0] border-[#1e3a5f]',
}

const CATEGORY_COLORS: Record<string, string> = {
  'AI': 'bg-purple-500/20 text-purple-300',
  'Data Centers': 'bg-blue-500/20 text-blue-300',
  'Startups': 'bg-emerald-500/20 text-emerald-300',
  'Investment': 'bg-[#FF9933]/20 text-[#FF9933]',
  'Roads': 'bg-amber-500/20 text-amber-300',
  'Power': 'bg-yellow-500/20 text-yellow-300',
  'Energy': 'bg-green-500/20 text-green-300',
  'Defence': 'bg-red-500/20 text-red-300',
  'Military': 'bg-red-500/20 text-red-300',
  'Economy': 'bg-cyan-500/20 text-cyan-300',
  'default': 'bg-[#1e3a5f]/40 text-[#8ba3c0]',
}

function getSourceColor(source: string): string {
  for (const [key, color] of Object.entries(SOURCE_COLORS)) {
    if (source.toLowerCase().includes(key.toLowerCase())) return color
  }
  return SOURCE_COLORS['default']
}

function getCategoryColor(category: string): string {
  for (const [key, color] of Object.entries(CATEGORY_COLORS)) {
    if (category.toLowerCase().includes(key.toLowerCase())) return color
  }
  return CATEGORY_COLORS['default']
}

function formatTimeAgo(dateStr: string): string {
  try {
    const date = parseISO(dateStr)
    if (!isValid(date)) return dateStr
    return formatDistanceToNow(date, { addSuffix: true })
  } catch {
    return dateStr
  }
}

const NewsCard: React.FC<NewsCardProps> = ({ item, compact = false }) => {
  const sourceColor = getSourceColor(item.source)
  const categoryColor = item.category ? getCategoryColor(item.category) : null
  const timeAgo = formatTimeAgo(item.publishedAt)

  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className={clsx(
        'card block group hover:border-[#FF9933]/50 hover:bg-[#0f2040] transition-all duration-200 cursor-pointer',
        compact ? 'p-3' : 'p-4'
      )}
    >
      {/* Badges row */}
      <div className="flex items-center gap-2 flex-wrap mb-2">
        <span
          className={clsx(
            'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border',
            sourceColor
          )}
        >
          {item.source}
        </span>
        {item.category && categoryColor && (
          <span
            className={clsx(
              'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium',
              categoryColor
            )}
          >
            {item.category}
          </span>
        )}
      </div>

      {/* Title */}
      <p
        className={clsx(
          'text-[#e8f0fe] font-medium leading-snug group-hover:text-white transition-colors',
          compact ? 'text-xs line-clamp-2' : 'text-sm line-clamp-2'
        )}
      >
        {item.title}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between mt-2 gap-2">
        <div className="flex items-center gap-1 text-[#8ba3c0] text-[11px]">
          <Clock className="w-3 h-3 flex-shrink-0" />
          <span>{timeAgo}</span>
        </div>
        <ExternalLink className="w-3 h-3 text-[#8ba3c0] group-hover:text-[#FF9933] transition-colors flex-shrink-0" />
      </div>
    </a>
  )
}

export default NewsCard
