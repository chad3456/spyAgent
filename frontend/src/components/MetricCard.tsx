import React from 'react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import clsx from 'clsx'
import type { LucideIcon } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string | null | undefined
  subtitle?: string
  trend?: number | null
  trendLabel?: string
  source?: string
  icon: LucideIcon
  iconColor?: string
  isLive?: boolean
  accentColor?: 'saffron' | 'green' | 'blue' | 'purple'
}

const ACCENT_MAP = {
  saffron: {
    border: 'border-l-[#FF9933]',
    iconBg: 'bg-[#FF9933]/10',
    iconColor: 'text-[#FF9933]',
  },
  green: {
    border: 'border-l-[#138808]',
    iconBg: 'bg-[#138808]/10',
    iconColor: 'text-[#138808]',
  },
  blue: {
    border: 'border-l-blue-500',
    iconBg: 'bg-blue-500/10',
    iconColor: 'text-blue-400',
  },
  purple: {
    border: 'border-l-purple-500',
    iconBg: 'bg-purple-500/10',
    iconColor: 'text-purple-400',
  },
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  trendLabel,
  source,
  icon: Icon,
  isLive = false,
  accentColor = 'saffron',
}) => {
  const accent = ACCENT_MAP[accentColor]

  const displayValue = value ?? '—'

  const TrendIcon =
    trend === null || trend === undefined
      ? Minus
      : trend > 0
      ? TrendingUp
      : trend < 0
      ? TrendingDown
      : Minus

  const trendColorClass =
    trend === null || trend === undefined
      ? 'text-[#8ba3c0]'
      : trend > 0
      ? 'text-emerald-400'
      : trend < 0
      ? 'text-red-400'
      : 'text-[#8ba3c0]'

  const trendText =
    trend === null || trend === undefined
      ? trendLabel ?? '—'
      : `${trend > 0 ? '+' : ''}${trend.toFixed(1)}%${trendLabel ? ` ${trendLabel}` : ''}`

  return (
    <div
      className={clsx(
        'card border-l-4 flex flex-col gap-3 hover:border-opacity-100 transition-all duration-200',
        accent.border
      )}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <span className="text-[#8ba3c0] text-xs font-medium uppercase tracking-wider leading-snug">
          {title}
        </span>
        <div className={clsx('p-2 rounded-lg flex-shrink-0', accent.iconBg)}>
          <Icon className={clsx('w-4 h-4', accent.iconColor)} />
        </div>
      </div>

      {/* Value */}
      <div className="flex items-end gap-2">
        <span className="metric-value text-2xl font-bold text-[#e8f0fe] leading-none">
          {displayValue}
        </span>
        {isLive && (
          <span className="mb-0.5 flex-shrink-0">
            <span className="live-dot inline-block" />
          </span>
        )}
      </div>

      {/* Subtitle */}
      {subtitle && (
        <span className="text-[#8ba3c0] text-xs">{subtitle}</span>
      )}

      {/* Trend */}
      {(trend !== undefined || trendLabel !== undefined) && (
        <div className={clsx('flex items-center gap-1 text-xs font-medium', trendColorClass)}>
          <TrendIcon className="w-3.5 h-3.5 flex-shrink-0" />
          <span>{trendText}</span>
        </div>
      )}

      {/* Source */}
      {source && (
        <span className="text-[#8ba3c0] text-[10px] mt-auto">
          Source: {source}
        </span>
      )}
    </div>
  )
}

export default MetricCard
