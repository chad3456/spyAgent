import React from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { Zap, Leaf, AlertCircle, RefreshCw } from 'lucide-react'
import clsx from 'clsx'
import { fetchInfrastructureData } from '../api/client'
import type { TimeSeriesPoint, NewsItem } from '../types'
import MetricCard from './MetricCard'
import NewsCard from './NewsCard'
import ChartCard from './ChartCard'
import { SectionSkeleton } from './LoadingSkeleton'

// ─── Helpers ──────────────────────────────────────────────────────────────────

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

function getLastYear(series: TimeSeriesPoint[]): number | null {
  const filtered = series.filter((p) => p.value !== null)
  if (filtered.length === 0) return null
  return filtered[filtered.length - 1].year
}

function last5(series: TimeSeriesPoint[]): Array<{ year: number; value: number }> {
  return series
    .filter((p): p is { year: number; value: number } => p.value !== null)
    .slice(-5)
}

// ─── Custom tooltip ───────────────────────────────────────────────────────────

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
          {entry.name}: {entry.value.toFixed(2)}{unit}
        </p>
      ))}
    </div>
  )
}

// ─── Category filter for news ─────────────────────────────────────────────────

const INFRA_CATEGORIES = ['All', 'Roads', 'Power', 'Energy', 'Railways', 'Urban']

function filterNewsByCategory(news: NewsItem[], category: string): NewsItem[] {
  if (category === 'All') return news
  const q = category.toLowerCase()
  return news.filter(
    (item) =>
      item.title.toLowerCase().includes(q) ||
      (item.category ?? '').toLowerCase().includes(q)
  )
}

// ─── Error state ──────────────────────────────────────────────────────────────

const ErrorState: React.FC<{ message: string; onRetry: () => void }> = ({
  message,
  onRetry,
}) => (
  <div className="flex flex-col items-center justify-center py-16 gap-4">
    <AlertCircle className="w-12 h-12 text-red-400" />
    <div className="text-center">
      <p className="text-[#e8f0fe] font-semibold mb-1">Failed to load infrastructure data</p>
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

// ─── Main component ───────────────────────────────────────────────────────────

const InfraSection: React.FC = () => {
  const [activeCategory, setActiveCategory] = React.useState('All')

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['infrastructure'],
    queryFn: fetchInfrastructureData,
    refetchInterval: 5 * 60 * 1000,
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading) return <SectionSkeleton />
  if (isError) {
    const msg = error instanceof Error ? error.message : 'Unknown error'
    return <ErrorState message={msg} onRetry={() => refetch()} />
  }
  if (!data) return null

  const powerLast = getLastValue(data.power)
  const powerTrend = getTrend(data.power)
  const powerYear = getLastYear(data.power)

  const renewableLast = getLastValue(data.renewable)
  const renewableTrend = getTrend(data.renewable)
  const renewableYear = getLastYear(data.renewable)

  const powerData = last5(data.power)
  const renewableData = last5(data.renewable)

  const filteredNews = filterNewsByCategory(data.news ?? [], activeCategory)

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Electric Power Consumption"
          value={powerLast !== null ? `${powerLast.toFixed(0)} kWh` : '—'}
          subtitle={powerYear ? `per capita, ${powerYear}` : undefined}
          trend={powerTrend}
          trendLabel="YoY"
          icon={Zap}
          accentColor="saffron"
          source="World Bank"
          isLive
        />
        <MetricCard
          title="Renewable Energy"
          value={renewableLast !== null ? `${renewableLast.toFixed(1)}%` : '—'}
          subtitle={renewableYear ? `of total output, ${renewableYear}` : undefined}
          trend={renewableTrend}
          trendLabel="YoY"
          icon={Leaf}
          accentColor="green"
          source="World Bank"
          isLive
        />
        {/* Placeholder cards if only 2 series */}
        <div className="card gradient-border-saffron flex flex-col justify-center gap-2 col-span-2 lg:col-span-2">
          <p className="text-[#8ba3c0] text-xs font-medium uppercase tracking-wider">
            Infrastructure Highlights
          </p>
          <p className="text-[#e8f0fe] text-sm leading-relaxed">
            India is expanding its national highway network, aiming for 200 GW of solar
            capacity by 2030 and deploying high-speed rail corridors.
          </p>
          <p className="text-[#8ba3c0] text-[10px]">Source: Ministry of Road Transport & MNRE</p>
        </div>
      </div>

      {/* Charts + News */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Charts */}
        <div className="xl:col-span-2 space-y-6">
          {/* Power consumption chart */}
          <ChartCard
            title="Electric Power Consumption (kWh per capita)"
            source="World Bank"
            minHeight={220}
          >
            {powerData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={powerData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <defs>
                    <linearGradient id="powerGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#FF9933" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#FF9933" stopOpacity={0} />
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
                    width={48}
                    tickFormatter={(v) => `${v}`}
                  />
                  <Tooltip content={<DarkTooltip unit=" kWh" />} />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#FF9933"
                    strokeWidth={2.5}
                    fill="url(#powerGradient)"
                    name="Power (kWh/capita)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 text-[#8ba3c0] text-sm">
                No data available
              </div>
            )}
          </ChartCard>

          {/* Renewable energy chart */}
          <ChartCard
            title="Renewable Energy (% of Total Output)"
            source="World Bank"
            minHeight={220}
          >
            {renewableData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={renewableData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
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
                    stroke="#138808"
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: '#138808', strokeWidth: 0 }}
                    activeDot={{ r: 6 }}
                    name="Renewable %"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 text-[#8ba3c0] text-sm">
                No data available
              </div>
            )}
          </ChartCard>

          {/* Combined overlay chart */}
          {powerData.length > 0 && renewableData.length > 0 && (
            <ChartCard
              title="Power vs Renewable Trend (Normalized)"
              source="World Bank"
              minHeight={220}
            >
              <ResponsiveContainer width="100%" height={220}>
                <LineChart
                  data={powerData.map((p) => {
                    const r = renewableData.find((r) => r.year === p.year)
                    return {
                      year: p.year,
                      power: p.value,
                      renewable: r?.value ?? null,
                    }
                  })}
                  margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
                  <XAxis
                    dataKey="year"
                    tick={{ fill: '#8ba3c0', fontSize: 11 }}
                    axisLine={{ stroke: '#1e3a5f' }}
                    tickLine={false}
                  />
                  <YAxis
                    yAxisId="left"
                    tick={{ fill: '#8ba3c0', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    width={48}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tick={{ fill: '#8ba3c0', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v) => `${v}%`}
                    width={40}
                  />
                  <Tooltip />
                  <Legend
                    wrapperStyle={{ color: '#8ba3c0', fontSize: '11px', paddingTop: '8px' }}
                  />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="power"
                    stroke="#FF9933"
                    strokeWidth={2}
                    dot={false}
                    name="Power (kWh)"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="renewable"
                    stroke="#138808"
                    strokeWidth={2}
                    dot={false}
                    name="Renewable %"
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          )}
        </div>

        {/* News feed */}
        <div className="xl:col-span-1">
          <div className="sticky top-4">
            <h3 className="text-[#e8f0fe] font-semibold text-sm mb-3 flex items-center gap-2">
              <span className="w-2 h-2 bg-[#FF9933] rounded-full" />
              Infrastructure News
            </h3>

            {/* Category filter */}
            <div className="flex flex-wrap gap-2 mb-4">
              {INFRA_CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={clsx(
                    'px-2.5 py-1 rounded-full text-[10px] font-medium border transition-all',
                    activeCategory === cat
                      ? 'bg-[#FF9933]/20 text-[#FF9933] border-[#FF9933]/40'
                      : 'bg-transparent border-[#1e3a5f] text-[#8ba3c0] hover:border-[#2a5080]'
                  )}
                >
                  {cat}
                </button>
              ))}
            </div>

            {filteredNews.length > 0 ? (
              <div className="space-y-3 max-h-[900px] overflow-y-auto pr-1">
                {filteredNews.slice(0, 12).map((item, i) => (
                  <NewsCard key={i} item={item} compact />
                ))}
              </div>
            ) : (
              <div className="card text-center text-[#8ba3c0] text-sm py-8">
                No news for this category
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default InfraSection
