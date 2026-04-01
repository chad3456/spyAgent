import React from 'react'
import clsx from 'clsx'

interface ChartCardProps {
  title: string
  source?: string
  children: React.ReactNode
  className?: string
  minHeight?: number
  action?: React.ReactNode
}

const ChartCard: React.FC<ChartCardProps> = ({
  title,
  source,
  children,
  className,
  minHeight = 240,
  action,
}) => {
  return (
    <div className={clsx('card flex flex-col gap-4', className)}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-0.5">
          <h3 className="text-[#e8f0fe] font-semibold text-sm">{title}</h3>
          {source && (
            <span className="text-[#8ba3c0] text-[10px]">Source: {source}</span>
          )}
        </div>
        {action && <div className="flex-shrink-0">{action}</div>}
      </div>

      {/* Chart content */}
      <div className="chart-container" style={{ minHeight }}>
        {children}
      </div>
    </div>
  )
}

export default ChartCard
