import React from 'react'
import clsx from 'clsx'
import type { ThreatLevel } from '../types/protest'
import { THREAT_CONFIG } from '../types/protest'

interface ThreatBadgeProps {
  level: ThreatLevel
  size?: 'sm' | 'md' | 'lg'
  showDot?: boolean
}

export const ThreatBadge: React.FC<ThreatBadgeProps> = ({
  level,
  size = 'md',
  showDot = true,
}) => {
  const cfg = THREAT_CONFIG[level]

  const sizeClasses = {
    sm: 'text-[9px] px-1.5 py-0.5 gap-1',
    md: 'text-[10px] px-2 py-1 gap-1.5',
    lg: 'text-xs px-3 py-1.5 gap-2',
  }

  const dotSize = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2.5 h-2.5',
  }

  return (
    <span
      className={clsx(
        'inline-flex items-center font-bold rounded uppercase tracking-wider border',
        sizeClasses[size]
      )}
      style={{
        color: cfg.color,
        backgroundColor: cfg.bg,
        borderColor: cfg.border,
      }}
    >
      {showDot && (
        <span
          className={clsx('rounded-full flex-shrink-0', dotSize[size], cfg.pulse && 'animate-pulse')}
          style={{ backgroundColor: cfg.color }}
        />
      )}
      {cfg.label}
    </span>
  )
}

export default ThreatBadge
