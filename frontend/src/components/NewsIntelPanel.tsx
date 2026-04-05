import React, { useState } from 'react'
import { ExternalLink } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import type { NewsIntelResponse, NewsArticle } from '../types/osint'

interface NewsIntelPanelProps {
  data: NewsIntelResponse | null
  loading: boolean
}

const CATEGORY_COLORS: Record<string, string> = {
  geopolitics: '#ffd60a',
  defense: '#ff2d55',
  conflict: '#ff6b35',
  cyber: '#bf5af2',
  diplomacy: '#5ac8fa',
  military: '#ff9f0a',
}

function ArticleCard({ article }: { article: NewsArticle }) {
  const timeAgo = (() => {
    try {
      return formatDistanceToNow(new Date(article.publishedAt), { addSuffix: true })
    } catch {
      return article.publishedAt
    }
  })()

  const catColor = CATEGORY_COLORS[article.category?.toLowerCase()] ?? '#64d2ff'

  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block px-4 py-3 border-b border-[#1e3a5f]/50 hover:bg-[#1e3a5f]/20 transition-colors group"
    >
      <div className="flex items-start gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-1">
            <span
              className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded"
              style={{ backgroundColor: `${catColor}22`, color: catColor }}
            >
              {article.category || 'news'}
            </span>
            <span className="text-[#8ba3c0] text-[9px]">{article.source}</span>
          </div>
          <p className="text-[#e8f0fe] text-xs font-medium leading-tight line-clamp-2 group-hover:text-white">
            {article.title}
          </p>
          {article.description && (
            <p className="text-[#8ba3c0] text-[11px] mt-1 leading-tight line-clamp-2">
              {article.description}
            </p>
          )}
          <div className="flex items-center gap-2 mt-1.5">
            <span className="text-[#8ba3c0]/60 text-[10px]">{timeAgo}</span>
            {article.country && (
              <span className="text-[#8ba3c0]/60 text-[10px]">• {article.country}</span>
            )}
            <ExternalLink className="w-2.5 h-2.5 text-[#8ba3c0]/40 ml-auto group-hover:text-[#64d2ff]" />
          </div>
        </div>
      </div>
    </a>
  )
}

export const NewsIntelPanel: React.FC<NewsIntelPanelProps> = ({ data, loading }) => {
  const [activeCategory, setActiveCategory] = useState<string>('all')

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="w-6 h-6 border-2 border-[#ffd60a] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!data) return null

  const categories = ['all', ...Object.keys(data.categories ?? {})]
  const articles =
    activeCategory === 'all'
      ? data.articles ?? []
      : data.categories?.[activeCategory] ?? []

  return (
    <div className="flex flex-col h-full">
      {/* Category tabs */}
      <div className="flex gap-1 px-3 py-2 border-b border-[#1e3a5f] overflow-x-auto flex-shrink-0">
        {categories.map((cat) => {
          const color = CATEGORY_COLORS[cat] ?? '#64d2ff'
          const isActive = activeCategory === cat
          return (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className="flex-shrink-0 text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded transition-all"
              style={{
                backgroundColor: isActive ? `${color}22` : 'transparent',
                color: isActive ? color : '#8ba3c0',
                border: `1px solid ${isActive ? color : 'transparent'}`,
              }}
            >
              {cat}
            </button>
          )
        })}
      </div>

      {/* Stats */}
      <div className="px-4 py-2 border-b border-[#1e3a5f]/50 flex-shrink-0">
        <span className="text-[10px] text-[#8ba3c0]">
          {articles.length} articles from {data.summary?.sources?.length ?? 0} sources
        </span>
      </div>

      {/* Articles */}
      <div className="flex-1 overflow-y-auto">
        {articles.length === 0 ? (
          <div className="flex items-center justify-center h-24">
            <span className="text-[#8ba3c0] text-xs">No articles available</span>
          </div>
        ) : (
          articles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))
        )}
      </div>
    </div>
  )
}
