import React from 'react'

interface SkeletonBlockProps {
  className?: string
}

const SkeletonBlock: React.FC<SkeletonBlockProps> = ({ className = '' }) => (
  <div className={`skeleton rounded ${className}`} />
)

export const MetricCardSkeleton: React.FC = () => (
  <div className="card flex flex-col gap-3">
    <div className="flex items-center justify-between">
      <SkeletonBlock className="h-4 w-24" />
      <SkeletonBlock className="h-8 w-8 rounded-full" />
    </div>
    <SkeletonBlock className="h-8 w-32" />
    <div className="flex items-center gap-2">
      <SkeletonBlock className="h-4 w-16" />
      <SkeletonBlock className="h-4 w-20" />
    </div>
    <SkeletonBlock className="h-3 w-28" />
  </div>
)

export const ChartCardSkeleton: React.FC = () => (
  <div className="card flex flex-col gap-4">
    <div className="flex items-center justify-between">
      <SkeletonBlock className="h-5 w-40" />
      <SkeletonBlock className="h-4 w-24" />
    </div>
    <SkeletonBlock className="h-48 w-full rounded-lg" />
  </div>
)

export const NewsCardSkeleton: React.FC = () => (
  <div className="card flex flex-col gap-3">
    <div className="flex items-center gap-2">
      <SkeletonBlock className="h-5 w-16 rounded-full" />
      <SkeletonBlock className="h-4 w-24" />
    </div>
    <SkeletonBlock className="h-4 w-full" />
    <SkeletonBlock className="h-4 w-3/4" />
    <SkeletonBlock className="h-3 w-20" />
  </div>
)

export const SectionSkeleton: React.FC = () => (
  <div className="space-y-6">
    {/* Metric cards row */}
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <MetricCardSkeleton key={i} />
      ))}
    </div>

    {/* Charts row */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <ChartCardSkeleton />
      <ChartCardSkeleton />
    </div>

    {/* News feed */}
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {[...Array(6)].map((_, i) => (
        <NewsCardSkeleton key={i} />
      ))}
    </div>
  </div>
)

interface LoadingSkeletonProps {
  variant?: 'section' | 'metric' | 'chart' | 'news'
  count?: number
}

const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  variant = 'section',
  count = 1,
}) => {
  if (variant === 'section') return <SectionSkeleton />

  const Component =
    variant === 'metric'
      ? MetricCardSkeleton
      : variant === 'chart'
      ? ChartCardSkeleton
      : NewsCardSkeleton

  return (
    <>
      {[...Array(count)].map((_, i) => (
        <Component key={i} />
      ))}
    </>
  )
}

export default LoadingSkeleton
