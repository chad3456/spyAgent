import React, { useState } from 'react'
import { Play, Image, ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react'
import clsx from 'clsx'
import type { LiveStream, ProtestImage } from '../types/protest'

interface VideoPanelProps {
  streams: LiveStream[]
  images: ProtestImage[]
  loading: boolean
}

export const VideoPanel: React.FC<VideoPanelProps> = ({ streams, images, loading }) => {
  const [activeTab, setActiveTab] = useState<'streams' | 'images'>('streams')
  const [activeStreamIdx, setActiveStreamIdx] = useState(0)

  if (loading) {
    return (
      <div className="h-full flex flex-col gap-3 p-3">
        <div className="h-8 bg-[#1e3a5f]/30 rounded animate-pulse" />
        <div className="flex-1 bg-[#1e3a5f]/30 rounded animate-pulse" />
      </div>
    )
  }

  const currentStream = streams[activeStreamIdx]

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar */}
      <div className="flex border-b border-[#1e3a5f]">
        <button
          onClick={() => setActiveTab('streams')}
          className={clsx(
            'flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-all',
            activeTab === 'streams'
              ? 'border-red-500 text-red-400'
              : 'border-transparent text-[#8ba3c0] hover:text-[#e8f0fe]'
          )}
        >
          <Play className="w-3 h-3" />
          Live Feeds
          {streams.length > 0 && (
            <span className="bg-red-500 text-white text-[9px] px-1 rounded-full leading-none py-0.5">
              {streams.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('images')}
          className={clsx(
            'flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-all',
            activeTab === 'images'
              ? 'border-[#64d2ff] text-[#64d2ff]'
              : 'border-transparent text-[#8ba3c0] hover:text-[#e8f0fe]'
          )}
        >
          <Image className="w-3 h-3" />
          OSINT Images
          {images.length > 0 && (
            <span className="bg-[#1e3a5f] text-[#64d2ff] text-[9px] px-1 rounded-full leading-none py-0.5">
              {images.length}
            </span>
          )}
        </button>
      </div>

      {/* Streams tab */}
      {activeTab === 'streams' && (
        <div className="flex flex-col flex-1 overflow-hidden">
          {streams.length === 0 ? (
            <div className="flex-1 flex items-center justify-center text-[#8ba3c0] text-sm">
              No live streams available
            </div>
          ) : (
            <>
              {/* Stream title bar */}
              <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0a0f1e] border-b border-[#1e3a5f]">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                <span className="text-[#e8f0fe] text-xs font-medium truncate flex-1">
                  {currentStream?.title ?? 'Live Coverage'}
                </span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setActiveStreamIdx((i) => Math.max(0, i - 1))}
                    disabled={activeStreamIdx === 0}
                    className="p-0.5 text-[#8ba3c0] hover:text-[#e8f0fe] disabled:opacity-30 transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="text-[10px] text-[#8ba3c0]">
                    {activeStreamIdx + 1}/{streams.length}
                  </span>
                  <button
                    onClick={() => setActiveStreamIdx((i) => Math.min(streams.length - 1, i + 1))}
                    disabled={activeStreamIdx === streams.length - 1}
                    className="p-0.5 text-[#8ba3c0] hover:text-[#e8f0fe] disabled:opacity-30 transition-colors"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* YouTube embed */}
              {currentStream && (
                <div className="flex-1 relative bg-black">
                  <iframe
                    key={currentStream.id}
                    src={currentStream.embedUrl}
                    title={currentStream.title}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                    className="w-full h-full border-0"
                  />
                </div>
              )}

              {/* Stream selector dots */}
              <div className="flex items-center justify-center gap-1.5 py-2 border-t border-[#1e3a5f]">
                {streams.map((s, i) => (
                  <button
                    key={s.id}
                    onClick={() => setActiveStreamIdx(i)}
                    className={clsx(
                      'rounded-full transition-all',
                      i === activeStreamIdx
                        ? 'w-4 h-1.5 bg-red-500'
                        : 'w-1.5 h-1.5 bg-[#1e3a5f] hover:bg-[#8ba3c0]'
                    )}
                    title={s.title}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Images tab */}
      {activeTab === 'images' && (
        <div className="flex-1 overflow-y-auto">
          {images.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-[#8ba3c0] text-sm">
              No images available
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-1.5 p-2">
              {images.map((img, i) => (
                <a
                  key={i}
                  href={img.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group relative block rounded-lg overflow-hidden bg-[#0a0f1e] border border-[#1e3a5f] hover:border-[#64d2ff] transition-colors"
                >
                  <img
                    src={img.url}
                    alt={img.title}
                    className="w-full h-20 object-cover opacity-80 group-hover:opacity-100 transition-opacity"
                    onError={(e) => {
                      const el = e.target as HTMLImageElement
                      el.parentElement!.style.display = 'none'
                    }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-1.5">
                    <p className="text-white text-[9px] leading-tight line-clamp-2">{img.title}</p>
                  </div>
                  <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <ExternalLink className="w-3 h-3 text-white" />
                  </div>
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default VideoPanel
