import React from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import {
  DollarSign,
  TrendingUp,
  Globe,
  BarChart2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react'
import { fetchEconomicData } from '../api/client'
import type { TimeSeriesPoint } from '../types'
import MetricCard from './MetricCard'
import NewsCard from './NewsCard'
import ChartCard from './ChartCard'
import { SectionSkeleton } from './LoadingSkeleton'

// ─── Number formatters ───────────────────────────────────────────────────────

function formatGDP(value: number | null | undefined, unit?: string): string {
  if (value === null || value === undefined) return '—'
  // World Bank returns GDP in current USD; typical India GDP ~3.5T
  if (unit === 'current USD' || unit === 'USD') {
    const trillions = value / 1e12
    if (trillions >= 1) return `$${trillions.toFixed(2)}T`
    const billions = value / 1e9
    return `$${billions.toFixed(0)}B`
  }
  // If already in billions or has explicit unit label
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`
  return `$${value.toFixed(2)}`
}

function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return `${value.toFixed(1)}%`
}

function getLastValue(series: TimeSeriesPoint[]): number | null {
  if (!series || series.length === 0) return null
  const filtered = series.filter((p) => p.value !== null)
  if (filtered.length === 0) return null
  return filtered[filtered.length - 1].value
}

function getTrend(series: TimeSeriesPoint[]): number | null {
  const filtered = series.filter((p) => p.value !== null)
  if (filtered.length < 2) return null
  const prev = filtered[filtered.length - 2].value!
  const curr = filtered[filtered.length - 1].value!
  if (prev === 0) return null
  return ((curr - prev) / Math.abs(prev)) * 100
}

function last5(series: TimeSeriesPoint[]): Array<{ year: number; value: number }> {
  return series
    .filter((p): p is { year: number; value: number } => p.value !== null)
    .slice(-5)
}

// ─── Custom tooltip ──────────────────────────────────────────────────────────

const DarkTooltip = ({
  active,
  payload,
  label,
  unit = '',
}: {
  active?: boolean
  payload?: Array<{ value: number; color: string; name: string }>
  label?: string
  unit?: string
}) => {
  if (!active || !payload || payload.length === 0) return null
  return (
    <div className="bg-[#0d1b2e] border border-[#1e3a5f] rounded-lg p-3 shadow-xl text-sm">
      <p className="text-[#8ba3c0] mb-1">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} style={{ color: entry.color }} className="font-semibold">
          {`${entry.value.toFixed(2)}${unit}`}
        </p>
      ))}
    </div>
  )
}

// ─── Error state ─────────────────────────────────────────────────────────────

const ErrorState: React.FC<{ message: string; onRetry: () => void }> = ({
  message,
  onRetry,
}) => (
  <div className="flex flex-col items-center justify-center py-16 gap-4">
    <AlertCircle className="w-12 h-12 text-red-400" />
    <div className="text-center">
      <p className="text-[#e8f0fe] font-semibold mb-1">Failed to load economic data</p>
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

// ─── Main component ──────────────────────────────────────────────────────────

const EconomicSection: React.FC = () => {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['economic'],
    queryFn: fetchEconomicData,
    refetchInterval: 5 * 60 * 1000,
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading) return <SectionSkeleton />
  if (isError) {
    const msg = error instanceof Error ? error.message : 'Unknown error'
    return <ErrorState message={msg} onRetry={() => refetch()} />
  }
  if (!data) return null

  const gdpStr = data.gdp
    ? formatGDP(data.gdp.value, data.gdp.unit)
    : '—'
  const gdpSubtitle = data.gdp ? `FY ${data.gdp.year}` : undefined

  const gdpGrowthLast = getLastValue(data.gdpGrowth)
  const gdpGrowthTrend = getTrend(data.gdpGrowth)
  const gdpGrowthYear = data.gdpGrowth.filter((p) => p.value !== null).slice(-1)[0]?.year

  const fdiLast = getLastValue(data.fdi)
  const fdiTrend = getTrend(data.fdi)
  const fdiYear = data.fdi.filter((p) => p.value !== null).slice(-1)[0]?.year

  const inflationLast = getLastValue(data.inflation)
  const inflationTrend = getTrend(data.inflation)
  const inflationYear = data.inflation.filter((p) => p.value !== null).slice(-1)[0]?.year

  const gdpGrowthData = last5(data.gdpGrowth)
  const fdiData = last5(data.fdi)
  const inflationData = last5(data.inflation)

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="GDP (Nominal)"
          value={gdpStr}
          subtitle={gdpSubtitle}
          icon={DollarSign}
          accentColor="saffron"
          source="World Bank"
          isLive
        />
        <MetricCard
          title="GDP Growth"
          value={formatPercent(gdpGrowthLast)}
          subtitle={gdpGrowthYear ? `FY ${gdpGrowthYear}` : undefined}
          trend={gdpGrowthTrend}
          trendLabel="YoY"
          icon={TrendingUp}
          accentColor="green"
          source="World Bank"
          isLive
        />
        <MetricCard
          title="Net FDI Inflows"
          value={fdiLast !== null ? formatPercent(fdiLast) : '—'}
          subtitle={fdiYear ? `% of GDP, ${fdiYear}` : undefined}
          trend={fdiTrend}
          trendLabel="YoY"
          icon={Globe}
          accentColor="blue"
          source="World Bank"
          isLive
        />
        <MetricCard
          title="Inflation (CPI)"
          value={formatPercent(inflationLast)}
          subtitle={inflationYear ? `FY ${inflationYear}` : undefined}
          trend={inflationTrend}
          trendLabel="YoY"
          icon={BarChart2}
          accentColor="purple"
          source="World Bank"
          isLive
        />
      </div>

      {/* Additional indicators */}
      {data.indicators && data.indicators.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {data.indicators.map((ind, i) => (
            <div key={i} className="card gradient-border-saffron">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-[#8ba3c0] text-xs mb-1">{ind.name}</p>
                  <p className="text-[#e8f0fe] font-bold text-lg metric-value">
                    {ind.value !== null && ind.value !== undefined
                      ? `${ind.value.toFixed(ind.unit === '%' ? 1 : 0)}${ind.unit}`
                      : '—'}
                  </p>
                  <p className="text-[#8ba3c0] text-[10px] mt-1">
                    {ind.year} · {ind.source}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Charts + News */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Charts column */}
        <div className="xl:col-span-2 space-y-6">
          {/* GDP Growth Chart */}
          <ChartCard title="GDP Growth Rate (%)" source="World Bank" minHeight={220}>
            {gdpGrowthData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={gdpGrowthData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
                  <XAxis
                    dataKey="year"
                    tick={{ fill: '#8ba3c0', fontSize: 11 }}
                    axisLine={{ stroke: '#1e3a5f' }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#8ba3c0', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v) => `${v}%`}
                    width={40}
                  />
                  <Tooltip content={<DarkTooltip unit="%" />} />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#FF9933"
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: '#FF9933', strokeWidth: 0 }}
                    activeDot={{ r: 6, fill: '#FF9933' }}
                    name="GDP Growth"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 text-[#8ba3c0] text-sm">
                No data available
              </div>
            )}
          </ChartCard>

          {/* FDI Area Chart */}
          <ChartCard title="Net FDI Inflows (% of GDP)" source="World Bank" minHeight={220}>
            {fdiData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={fdiData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <defs>
                    <linearGradient id="fdiGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#138808" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#138808" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
                  <XAxis
                    dataKey="year"
                    tick={{ fill: '#8ba3c0', fontSize: 11 }}
                    axisLine={{ stroke: '#1e3a5f' }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#8ba3c0', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v) => `${v}%`}
                    width={40}
                  />
                  <Tooltip content={<DarkTooltip unit="%" />} />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#138808"
                    strokeWidth={2.5}
                    fill="url(#fdiGradient)"
                    name="FDI % GDP"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 text-[#8ba3c0] text-sm">
                No data available
              </div>
            )}
          </ChartCard>

          {/* Inflation Bar Chart */}
          <ChartCard title="Inflation, Consumer Prices (%)" source="World Bank" minHeight={220}>
            {inflationData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={inflationData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" vertical={false} />
                  <XAxis
                    dataKey="year"
                    tick={{ fill: '#8ba3c0', fontSize: 11 }}
                    axisLine={{ stroke: '#1e3a5f' }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#8ba3c0', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v) => `${v}%`}
                    width={40}
                  />
                  <Tooltip content={<DarkTooltip unit="%" />} />
                  <Bar
                    dataKey="value"
                    fill="#FF9933"
                    radius={[4, 4, 0, 0]}
                    maxBarSize={48}
                    name="Inflation"
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 text-[#8ba3c0] text-sm">
                No data available
              </div>
            )}
          </ChartCard>
        </div>

        {/* News feed column */}
        <div className="xl:col-span-1">
          <div className="sticky top-4">
            <h3 className="text-[#e8f0fe] font-semibold text-sm mb-3 flex items-center gap-2">
              <span className="w-2 h-2 bg-[#FF9933] rounded-full" />
              Economic News
            </h3>
            {data.news && data.news.length > 0 ? (
              <div className="space-y-3 max-h-[900px] overflow-y-auto pr-1">
                {data.news.slice(0, 10).map((item, i) => (
                  <NewsCard key={i} item={item} compact />
                ))}
              </div>
            ) : (
              <div className="card text-center text-[#8ba3c0] text-sm py-8">
                No news available
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default EconomicSection
